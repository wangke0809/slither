import json

from slither.core.cfg.node import NodeType, link_nodes
from slither.core.declarations import Function
from slither.core.expressions import (
    Literal,
    AssignmentOperation,
    AssignmentOperationType,
    Identifier, CallExpression, TupleExpression, BinaryOperation, UnaryOperation,
)
from slither.core.solidity_types import ElementaryType
from slither.exceptions import SlitherException
from slither.solc_parsing.yul.evm_functions import *
from slither.solc_parsing.yul.yul_variable import YulVariable

###################################################################################
###################################################################################
# region Block conversion
###################################################################################
###################################################################################

"""
The functions in this region, at a high level, will extract the control flow
structures and metadata from the input AST. These include things like function
definitions and local variables.

Each function takes three parameters:
    1)  root is a NodeSolc of NodeType.ASSEMBLY, and stores information at the
        local scope. In Yul, variables are scoped to the function they're
        declared in (except for variables outside the assembly block)
    2)  parent is the last node in the CFG. new nodes should be linked against
        this node
    3)  ast is a dictionary and is the current node in the Yul ast being converted
    
Each function must return a single parameter:
    1) A NodeSolc representing the new end of the CFG

The entrypoint is the function at the end of this region, `convert_yul`, which
dispatches to a specialized function based on a lookup dictionary.
"""


def convert_yul_block(root, parent, ast):
    for statement in ast["statements"]:
        parent = convert_yul(root, parent, statement)
    return parent


def convert_yul_function_definition(root, parent, ast):
    # todo this is so bad
    f = Function()
    f._contract = root.function.contract
    f._name = root.format_canonical_yul_name(ast['name'])
    f._contract_declarer = root.function.contract_declarer
    f._is_implemented = True
    f._counter_nodes = 0

    def new_node(node_type, src):
        node = root.function.new_node(node_type, src)
        node.set_function(f)
        node._node_id = f._counter_nodes
        root.function._counter_nodes -= 1
        root.function._nodes.pop()
        f._counter_nodes += 1
        f._nodes.append(node)
        return node

    f.new_node = new_node
    root.function.contract._functions[f._name] = f

    new_root = f.new_node(NodeType.ASSEMBLY, ast['src'])
    new_root.set_yul_child(root, ast['name'])
    f._entry_point = new_root

    node = f.new_node(NodeType.ENTRYPOINT, ast['src'])
    link_nodes(new_root, node)

    for param in ast.get('parameters', []):
        node = convert_yul(new_root, node, param)
        f._parameters.append(new_root.get_yul_local_variable_from_name(param['name']))

    for ret in ast.get('returnVariables', []):
        node = convert_yul(new_root, node, ret)
        f._returns.append(new_root.get_yul_local_variable_from_name(ret['name']))
    convert_yul(new_root, node, ast['body'])

    for node in f.nodes:
        node.analyze_expressions(f)

    return parent


def convert_yul_variable_declaration(root, parent, ast):
    for variable_ast in ast['variables']:
        parent = convert_yul(root, parent, variable_ast)

    node = parent.function.new_node(NodeType.EXPRESSION, ast["src"])  # todo should this be NodeType.VARIABLE
    node.add_unparsed_yul_expression(root, ast)
    link_nodes(parent, node)
    return node


def convert_yul_assignment(root, parent, ast):
    node = parent.function.new_node(NodeType.EXPRESSION, ast["src"])
    node.add_unparsed_yul_expression(root, ast)
    link_nodes(parent, node)
    return node


def convert_yul_expression_statement(root, parent, ast):
    src = ast['src']
    expression_ast = ast['expression']

    expression = parent.function.new_node(NodeType.EXPRESSION, src)
    expression.add_unparsed_yul_expression(root, expression_ast)
    link_nodes(parent, expression)

    return expression


def convert_yul_if(root, parent, ast):
    src = ast['src']
    condition_ast = ast['condition']
    body_ast = ast['body']

    condition = parent.function.new_node(NodeType.IF, src)
    condition.add_unparsed_yul_expression(root, condition_ast)

    body = convert_yul(root, condition, body_ast)
    end = parent.function.new_node(NodeType.ENDIF, src)

    link_nodes(parent, condition)
    link_nodes(condition, end)
    link_nodes(body, end)

    return end


def convert_yul_switch(root, parent, ast):
    """
    This is unfortunate. We don't really want a switch in our IR so we're going to
    translate it into a series of if statements.

    Note that the expression may be state-changing, and so we need to store it somewhere
    first
    """
    cases_ast = ast['cases']
    expression_ast = ast['expression']

    # These are the two temporary variables we're using. The first stores the result of
    # the expression being switched on, and the second stores whether a case was executed
    # so we know whether to enter the default case or not
    switch_expr_var = 'switch_expr_{}'.format(ast['src'].replace(':', '_'))
    switch_matched_var = 'switch_matched_{}'.format(ast['src'].replace(':', '_'))

    rewritten_switch = {
        'nodeType': 'YulBlock',
        'src': ast['src'],
        'statements': [
            {
                'nodeType': 'YulVariableDeclaration',
                'src': expression_ast['src'],
                'variables': [
                    {
                        'nodeType': 'YulTypedName',
                        'src': expression_ast['src'],
                        'name': switch_expr_var,
                        'type': '',
                    },
                ],
                'value': expression_ast,
            },
            {
                'nodeType': 'YulVariableDeclaration',
                'src': expression_ast['src'],
                'variables': [
                    {
                        'nodeType': 'YulTypedName',
                        'src': expression_ast['src'],
                        'name': switch_matched_var,
                        'type': '',
                    },
                ],
                'value': {
                    'nodeType': 'YulLiteral',
                    'src': expression_ast['src'],
                    'value': '0',
                    'type': '',
                },
            }
        ],
    }

    default_ast = None

    for case_ast in cases_ast:
        body_ast = case_ast['body']
        value_ast = case_ast['value']

        if value_ast == 'default':
            default_ast = case_ast
            continue

        rewritten_switch['statements'].append({
            'nodeType': 'YulIf',
            'src': case_ast['src'],
            'condition': {
                'nodeType': 'YulFunctionCall',
                'src': case_ast['src'],
                'functionName': {
                    'nodeType': 'YulIdentifier',
                    'src': case_ast['src'],
                    'name': 'eq',
                },
                'arguments': [
                    {
                        'nodeType': 'YulIdentifier',
                        'src': case_ast['src'],
                        'name': switch_expr_var,
                    },
                    value_ast,
                ]
            },
            'body': {
                'nodeType': 'YulBlock',
                'src': body_ast['src'],
                'statements': [
                    {
                        'nodeType': 'YulAssignment',
                        'src': body_ast['src'],
                        'variableNames': [
                            {
                                'nodeType': 'YulIdentifier',
                                'src': body_ast['src'],
                                'name': switch_matched_var,
                            }
                        ],
                        'value': {
                            'nodeType': 'YulLiteral',
                            'src': expression_ast['src'],
                            'value': '1',
                            'type': '',
                        },
                    },
                    body_ast,
                ]
            }
        })

    if default_ast:
        body_ast = default_ast['body']

        rewritten_switch['statements'].append({
            'nodeType': 'YulIf',
            'src': default_ast['src'],
            'condition': {
                'nodeType': 'YulFunctionCall',
                'src': default_ast['src'],
                'functionName': {
                    'nodeType': 'YulIdentifier',
                    'src': default_ast['src'],
                    'name': 'eq',
                },
                'arguments': [
                    {
                        'nodeType': 'YulIdentifier',
                        'src': default_ast['src'],
                        'name': switch_matched_var,
                    },
                    {
                        'nodeType': 'YulLiteral',
                        'src': default_ast['src'],
                        'value': '0',
                        'type': '',
                    },
                ]
            },
            'body': body_ast,
        })

    return convert_yul(root, parent, rewritten_switch)


def convert_yul_for_loop(root, parent, ast):
    pre_ast = ast['pre']
    condition_ast = ast['condition']
    post_ast = ast['post']
    body_ast = ast['body']

    start_loop = parent.function.new_node(NodeType.STARTLOOP, ast['src'])
    end_loop = parent.function.new_node(NodeType.ENDLOOP, ast['src'])

    link_nodes(parent, start_loop)

    pre = convert_yul(root, start_loop, pre_ast)

    condition = parent.function.new_node(NodeType.IFLOOP, condition_ast['src'])
    condition.add_unparsed_yul_expression(root, condition_ast)
    link_nodes(pre, condition)

    link_nodes(condition, end_loop)

    body = convert_yul(root, condition, body_ast)

    post = convert_yul(root, body, post_ast)

    link_nodes(post, condition)

    return end_loop


def convert_yul_break(root, parent, ast):
    break_ = parent.function.new_node(NodeType.BREAK, ast['src'])
    link_nodes(parent, break_)
    return break_


def convert_yul_continue(root, parent, ast):
    continue_ = parent.function.new_node(NodeType.CONTINUE, ast['src'])
    link_nodes(parent, continue_)
    return continue_


def convert_yul_leave(root, parent, ast):
    leave = parent.function.new_node(NodeType.RETURN, ast['src'])
    link_nodes(parent, leave)
    return leave


def convert_yul_typed_name(root, parent, ast):
    var = YulVariable(ast)
    var.set_function(root.function)
    var.set_offset(ast['src'], root.slither)

    root.add_yul_local_variable(var)

    return parent


def convert_yul_unsupported(root, parent, ast):
    raise SlitherException(f"no converter available for {ast['nodeType']} {json.dumps(ast, indent=2)}")


def convert_yul(root, parent, ast):
    return converters.get(ast['nodeType'], convert_yul_unsupported)(root, parent, ast)


converters = {
    'YulBlock': convert_yul_block,
    'YulFunctionDefinition': convert_yul_function_definition,
    'YulVariableDeclaration': convert_yul_variable_declaration,
    'YulAssignment': convert_yul_assignment,
    'YulExpressionStatement': convert_yul_expression_statement,
    'YulIf': convert_yul_if,
    'YulSwitch': convert_yul_switch,
    'YulForLoop': convert_yul_for_loop,
    'YulBreak': convert_yul_break,
    'YulContinue': convert_yul_continue,
    'YulLeave': convert_yul_leave,
    'YulTypedName': convert_yul_typed_name,
}

# endregion
###################################################################################
###################################################################################

###################################################################################
###################################################################################
# region Expression parsing
###################################################################################
###################################################################################

"""
The functions in this region parse the AST into expressions.

Each function takes three parameters:
    1)  root is the same root as above
    2)  node is the CFG node which stores this expression
    3)  ast is the same ast as above
    
Each function must return a single parameter:
    1) The operation that was parsed, or None

The entrypoint is the function at the end of this region, `parse_yul`, which
dispatches to a specialized function based on a lookup dictionary.
"""


def _parse_yul_assignment_common(root, node, ast, key):
    lhs = [parse_yul(root, node, arg) for arg in ast[key]]
    rhs = parse_yul(root, node, ast['value'])

    operation = AssignmentOperation(vars_to_val(lhs), rhs, AssignmentOperationType.ASSIGN, vars_to_typestr(lhs))
    operation.set_offset(ast["src"], root.slither)
    return operation


def parse_yul_variable_declaration(root, node, ast):
    """
    We already created variables in the conversion phase, so just do
    the assignment
    """

    if not ast['value']:
        return None

    return _parse_yul_assignment_common(root, node, ast, 'variables')


def parse_yul_assignment(root, node, ast):
    return _parse_yul_assignment_common(root, node, ast, 'variableNames')


def parse_yul_function_call(root, node, ast):
    args = [parse_yul(root, node, arg) for arg in ast['arguments']]
    function = parse_yul(root, node, ast['functionName'])

    if isinstance(function, YulBuiltin):
        name = function.name
        if name in binary_ops:
            return BinaryOperation(args[0], args[1], binary_ops[name])

        if name in unary_ops:
            return UnaryOperation(args[0], unary_ops[name])

        raise SlitherException(f"unsupported builtin {name}")
    elif isinstance(function, Identifier):
        return CallExpression(function, args, vars_to_typestr(function.value.returns))
    else:
        raise SlitherException(f"unexpected function call target type {str(type(function))}")


def parse_yul_identifier(root, node, ast):
    # todo handle _slot, _offset, and any other contract-scoped identifiers
    # https://solidity.readthedocs.io/en/v0.6.2/assembly.html#access-to-external-variables-functions-and-libraries
    name = ast['name']

    if name in builtins:
        return YulBuiltin(name)

    # check function-scoped variables first
    variable = root.function.get_local_variable_from_name(name)
    if variable:
        return Identifier(variable)

    # check yul-scoped variable
    variable = root.get_yul_local_variable_from_name(name)
    if variable:
        return Identifier(variable)

    # check yul-scoped function
    # note that a function can recurse into itself, so we have two canonical names
    # to check (but only one of them can be valid)

    functions = root.function.contract_declarer._functions

    canonical_name = root.format_canonical_yul_name(name)
    if canonical_name in functions:
        return Identifier(functions[canonical_name])

    canonical_name = root.format_canonical_yul_name(name, -1)
    if canonical_name in functions:
        return Identifier(functions[canonical_name])

    raise SlitherException(f"unresolved reference to identifier {name}")


def parse_yul_literal(root, node, ast):
    type_ = ast['type']
    value = ast['value']

    if not type_:
        type_ = 'bool' if value in ['true', 'false'] else 'uint256'

    return Literal(value, ElementaryType(type_))


def parse_yul_typed_name(root, node, ast):
    var = root.get_yul_local_variable_from_name(ast['name'])

    i = Identifier(var)
    i._type = var.type
    return i


def parse_yul_unsupported(root, node, ast):
    raise SlitherException(f"no parser available for {ast['nodeType']} {json.dumps(ast, indent=2)}")


def parse_yul(root, node, ast):
    return parsers.get(ast['nodeType'], parse_yul_unsupported)(root, node, ast)


parsers = {
    'YulVariableDeclaration': parse_yul_variable_declaration,
    'YulAssignment': parse_yul_assignment,
    'YulFunctionCall': parse_yul_function_call,
    'YulIdentifier': parse_yul_identifier,
    'YulTypedName': parse_yul_typed_name,
    'YulLiteral': parse_yul_literal,
}


# endregion
###################################################################################
###################################################################################

def vars_to_typestr(rets):
    if len(rets) == 1:
        return str(rets[0].type)
    return "tuple({})".format(",".join(str(ret.type) for ret in rets))


def vars_to_val(vars):
    if len(vars) == 1:
        return vars[0]
    return TupleExpression(vars)
