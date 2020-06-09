from slither.core.cfg.node import Node
from slither.core.cfg.node import NodeType
from slither.solc_parsing.expressions.expression_parsing import parse_expression
from slither.solc_parsing.yul.parse_yul import parse_yul
from slither.visitors.expression.read_var import ReadVar
from slither.visitors.expression.write_var import WriteVar
from slither.visitors.expression.find_calls import FindCalls

from slither.visitors.expression.export_values import ExportValues
from slither.core.declarations.solidity_variables import SolidityVariable, SolidityFunction
from slither.core.declarations.function import Function

from slither.core.variables.state_variable import StateVariable

from slither.core.expressions.identifier import Identifier
from slither.core.expressions.assignment_operation import AssignmentOperation, AssignmentOperationType

class NodeSolc(Node):

    def __init__(self, nodeType, nodeId):
        super(NodeSolc, self).__init__(nodeType, nodeId)
        self._unparsed_expression = None
        self._unparsed_yul_expression = None

        """
        todo this should really go somewhere else, but until
        that happens I'm setting it to None for performance
        """
        self._yul_local_variables = None
        self._yul_local_functions = None
        self._yul_path = None

    def set_yul_root(self, func):
        self._yul_path = [func.name, f"asm_{func._counter_asm_nodes}"]

    def set_yul_child(self, parent, cur):
        self._yul_path = parent.yul_path +  [cur]

    @property
    def yul_path(self):
        return self._yul_path

    def format_canonical_yul_name(self, name, off=None):
        return ".".join(self._yul_path[:off] + [name])

    def add_yul_local_variable(self, var):
        if not self._yul_local_variables:
            self._yul_local_variables = []
        self._yul_local_variables.append(var)

    def get_yul_local_variable_from_name(self, variable_name):
        return next((v for v in self._yul_local_variables if v.name == variable_name), None)

    def add_yul_local_function(self, func):
        if not self._yul_local_functions:
            self._yul_local_functions = []
        self._yul_local_functions.append(func)

    def get_yul_local_function_from_name(self, func_name):
        return next((v for v in self._yul_local_functions if v.name == func_name), None)

    def add_unparsed_expression(self, expression):
        assert self._unparsed_expression is None
        self._unparsed_expression = expression

    def add_unparsed_yul_expression(self, root, expression):
        assert self._unparsed_expression is None
        self._unparsed_yul_expression = (root, expression)

    def analyze_expressions(self, caller_context):
        if self.type == NodeType.VARIABLE and not self._expression:
            self._expression = self.variable_declaration.expression
        if self._unparsed_expression:
            expression = parse_expression(self._unparsed_expression, caller_context)
            self._expression = expression
            self._unparsed_expression = None

        if self._unparsed_yul_expression:
            expression = parse_yul(self._unparsed_yul_expression[0], self, self._unparsed_yul_expression[1])
            self._expression = expression
            self._unparsed_yul_expression = None

        if self.expression:

            if self.type == NodeType.VARIABLE:
                # Update the expression to be an assignement to the variable
                #print(self.variable_declaration)
                _expression = AssignmentOperation(Identifier(self.variable_declaration),
                                                  self.expression,
                                                  AssignmentOperationType.ASSIGN,
                                                  self.variable_declaration.type)
                _expression.set_offset(self.expression.source_mapping, self.slither)
                self._expression = _expression

            expression = self.expression
            pp = ReadVar(expression)
            self._expression_vars_read = pp.result()

#            self._vars_read = [item for sublist in vars_read for item in sublist]
#            self._state_vars_read = [x for x in self.variables_read if\
#                                     isinstance(x, (StateVariable))]
#            self._solidity_vars_read = [x for x in self.variables_read if\
#                                        isinstance(x, (SolidityVariable))]

            pp = WriteVar(expression)
            self._expression_vars_written = pp.result()

#            self._vars_written = [item for sublist in vars_written for item in sublist]
#            self._state_vars_written = [x for x in self.variables_written if\
#                                        isinstance(x, StateVariable)]

            pp = FindCalls(expression)
            self._expression_calls = pp.result()
            self._external_calls_as_expressions = [c for c in self.calls_as_expression if not isinstance(c.called, Identifier)]
            self._internal_calls_as_expressions = [c for c in self.calls_as_expression if isinstance(c.called, Identifier)]

