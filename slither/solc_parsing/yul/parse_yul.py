from typing import Dict, TYPE_CHECKING

from slither.core.cfg.node import NodeType, link_nodes
from slither.core.expressions import (
    Literal,
    AssignmentOperation,
    AssignmentOperationType,
    Identifier,
)
from slither.core.solidity_types import ElementaryType
from slither.exceptions import SlitherException

# Avoid ciruclar import
if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.solc_parsing.cfg.node import NodeSolc

###################################################################################
###################################################################################
# region Block parsing
###################################################################################
###################################################################################


def parse_yul(yul_ast: Dict, predecessor: "NodeSolc") -> "NodeSolc":
    """

    :param yul_ast: AST
    :param node: Predecessor node
    :return: New node. If multiple node are created (eg. if), return the ending node
    """
    if yul_ast["nodeType"] == "YulBlock":
        # Todo: handle YulBlock without statements
        assert "statements" in yul_ast and yul_ast["statements"]

        for statement in yul_ast["statements"]:
            new_node = predecessor.function.new_node(NodeType.ASSEMBLY, statement["src"])
            new_node.add_unparsed_yul_expression(statement)
            link_nodes(predecessor, new_node)
        return new_node

    # Probably CFG-related  stuff like If/Loop
    raise SlitherException(f"{yul_ast['NodeType']} not hanlded")


# endregion
###################################################################################
###################################################################################
# region Expression parsing
###################################################################################
###################################################################################


def parse_yul_expression(expression: Dict, context: "NodeSolc") -> "Expression":
    """
    Call by NodeSolc.analyze_expressions

    :param expression: Expression's AST
    :param context: Node of the expression
    :return:
    """

    if expression["nodeType"] == "YulAssignment":
        left_variable_value = expression["variableNames"][0]  # Todo: handle tuple
        left_variable = _parse_value(left_variable_value, context)

        right_variable = _parse_value(expression["value"], context)

        operation = AssignmentOperation(
            left_variable, right_variable, AssignmentOperationType.ASSIGN, ElementaryType("uint256")
        )
        operation.set_offset(expression["src"], context.slither)
        return operation

    raise SlitherException(f"Expression {expression['NodeType']} not hanlded")


def _parse_value(value: Dict, context: "NodeSolc") -> "Expression":
    """

    :param value:
    :param context:
    :return:
    """
    if value["nodeType"] == "YulIdentifier":
        variable = context.function.get_local_variable_from_name(value["name"])
        assert variable  # Assume the variable is a known local variable
        return Identifier(variable)

    elif value["nodeType"] == "YulLiteral":
        return Literal(
            value["value"], ElementaryType("uint256")
        )  # Assume here that everything is an uint256

    raise SlitherException(f"Expression {value['NodeType']} not hanlded")


# endregion
###################################################################################
###################################################################################
