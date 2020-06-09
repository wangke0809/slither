from slither.core.cfg.node import NodeType, link_nodes
from slither.core.declarations import Function
from slither.core.expressions import (
    Literal,
    AssignmentOperation,
    AssignmentOperationType,
    Identifier, CallExpression, TupleExpression, BinaryOperationType, BinaryOperation,
)
from slither.core.solidity_types import ElementaryType
from slither.exceptions import SlitherException
from slither.solc_parsing.yul.yul_variable import YulVariable


###################################################################################
###################################################################################
# region Block conversion
###################################################################################
###################################################################################

def convert_yul(root, parent, ast):
    print(f"converting {ast['nodeType']}", ast)
    return converters[ast['nodeType']](root, parent, ast)


def convert_yul_expression(root, parent, ast):
    node = root.function.new_node(NodeType.EXPRESSION, ast["src"])
    node.add_unparsed_yul_expression(root, ast)
    link_nodes(parent, node)
    return node


def convert_yul_function_definition(root, parent, ast):
    params = [parse_yul(root, parent, param) for param in ast['parameters']] if 'parameters' in ast else []
    rets = [parse_yul(root, parent, ret) for ret in ast['returnVariables']] if 'returnVariables' in ast else []

    f = Function()
    f._contract_declarer = root.function.contract
    f._name = ast['name']
    f._parameters = params
    f._returns = rets

    root.add_yul_local_function(f)

    return parent


def convert_yul_expression_statement(root, parent, ast):
    src = ast['src']
    expression_ast = ast['expression']

    expression = root.function.new_node(NodeType.EXPRESSION, src)
    expression.add_unparsed_yul_expression(root, expression_ast)
    link_nodes(parent, expression)

    return expression


def convert_yul_block(root, parent, ast):
    for statement in ast["statements"]:
        parent = convert_yul(root, parent, statement)
    return parent


def convert_yul_if(root, parent, ast):
    src = ast['src']
    condition_ast = ast['condition']
    body_ast = ast['body']

    condition = root.function.new_node(NodeType.IF, src)
    condition.add_unparsed_yul_expression(root, condition_ast)

    body = convert_yul(root, condition, body_ast)
    end = root.function.new_node(NodeType.ENDIF, src)

    link_nodes(parent, condition)
    link_nodes(condition, end)
    link_nodes(body, end)

    return end


converters = {
    'YulVariableDeclaration': convert_yul_expression,
    'YulFunctionDefinition': convert_yul_function_definition,
    'YulExpressionStatement': convert_yul_expression_statement,
    'YulAssignment': convert_yul_expression,
    'YulBlock': convert_yul_block,
    'YulIf': convert_yul_if,
}


# endregion
###################################################################################
###################################################################################
# region Expression parsing
###################################################################################
###################################################################################


def parse_yul(root, node, ast):
    print(f"parsing {ast['nodeType']}", ast)

    return parsers[ast['nodeType']](root, node, ast)


def parse_yul_identifier(root, node, ast):
    name = ast['name']

    # check function-scoped variables first
    variable = root.function.get_local_variable_from_name(name)
    if variable:
        return Identifier(variable)

    # check yul-scoped variable
    variable = root.get_yul_local_variable_from_name(name)
    if variable:
        return Identifier(variable)

    raise SlitherException(f"unresolved reference to variable {name}")


def parse_yul_literal(root, node, ast):
    type_ = ast['type']
    if not type_:
        type_ = 'uint256'

    value = ast['value']

    return Literal(value, ElementaryType(type_))


def parse_yul_typed_name(root, node, ast):
    var = YulVariable(ast)
    var.set_function(root.function)
    var.set_offset(ast['src'], root.slither)

    root.add_yul_local_variable(var)

    i = Identifier(var)
    i._type = 'uint256'
    return i


def parse_yul_variable_declaration(root, node, ast):
    """
        A YulVariableDeclaration has one or more YulTypedName nodes
        in the `variables` field.

        Example:
            let x
            let a, b

        If the variable declaration has an associated value, that's
        stored in the `value` field. The value will either be a
        `YulLiteral` node, a `YulIdentifier` node, or a
        `YulFunctionCall` node.

        Example:
            let y := 5
            let z := y
            let val, ok := func()
    """

    vars = [parse_yul(root, node, var) for var in ast['variables']]

    if not ast['value']:
        return None

    right_variable = parse_yul(root, node, ast['value'])

    # Yul doesn't support multiple non-function assignments... for now
    if not isinstance(right_variable, CallExpression):
        assert (len(vars) == 1)

        operation = AssignmentOperation(
            vars[0], right_variable, AssignmentOperationType.ASSIGN, ElementaryType("uint256")
        )
    else:
        operation = AssignmentOperation(
            TupleExpression(vars), right_variable, AssignmentOperationType.ASSIGN, vars_to_typestr(vars)
        )

    operation.set_offset(ast["src"], root.slither)
    return operation


def parse_yul_function_call(root, node, ast):
    # todo parse the functionName and get a function back
    args = ast['arguments']
    function_name_node = ast['functionName']

    binary_ops = {
        'add': BinaryOperationType.ADDITION,
        'sub': BinaryOperationType.SUBTRACTION,
        'mul': BinaryOperationType.MULTIPLICATION,
        'div': BinaryOperationType.DIVISION,
        'sdiv': BinaryOperationType.DIVISION,
        'mod': BinaryOperationType.MODULO,
        'smod': BinaryOperationType.MODULO,
        'exp': BinaryOperationType.POWER,
        'lt': BinaryOperationType.LESS,
        'gt': BinaryOperationType.GREATER,
        'slt': BinaryOperationType.LESS,
        'sgt': BinaryOperationType.GREATER,
        'eq': BinaryOperationType.EQUAL,
        'and': BinaryOperationType.AND,
        'or': BinaryOperationType.OR,
        'xor': BinaryOperationType.CARET,
        # 'byte': ???
        'shl': BinaryOperationType.LEFT_SHIFT,
        'shr': BinaryOperationType.RIGHT_SHIFT,
        'sar': BinaryOperationType.RIGHT_SHIFT,
    }

    name = function_name_node['name']
    if name in binary_ops:
        assert (len(args) == 2)

        return BinaryOperation(parse_yul(root, node, args[0]), parse_yul(root, node, args[1]), binary_ops[name])

    f = root.get_yul_local_function_from_name(name)
    return CallExpression(Identifier(f), [parse_yul(root, node, arg) for arg in args], vars_to_typestr(f.returns))


def parse_yul_assignment(root, node, ast):
    lhs = [parse_yul(root, node, arg) for arg in ast['variableNames']]
    rhs = parse_yul(root, node, ast['value'])

    if len(lhs) == 1:
        operation = AssignmentOperation(
            lhs[0], rhs, AssignmentOperationType.ASSIGN, ElementaryType("uint256")
        )
    else:
        operation = AssignmentOperation(
            TupleExpression(lhs), rhs, AssignmentOperationType.ASSIGN, ElementaryType("uint256")
        )
    operation.set_offset(ast["src"], root.slither)
    return operation


parsers = {
    'YulIdentifier': parse_yul_identifier,
    'YulLiteral': parse_yul_literal,
    'YulVariableDeclaration': parse_yul_variable_declaration,
    'YulAssignment': parse_yul_assignment,
    'YulFunctionCall': parse_yul_function_call,
    'YulTypedName': parse_yul_typed_name,
}


# endregion
###################################################################################
###################################################################################

def vars_to_typestr(rets):
    if len(rets) == 1:
        return rets[0].type
    return "tuple({})".format(",".join(ret.type for ret in rets))
