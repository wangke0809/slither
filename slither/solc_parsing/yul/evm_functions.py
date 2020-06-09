from slither.core.expressions import BinaryOperationType, UnaryOperationType
from slither.core.expressions.expression import Expression

unclassified = [
    'stop',
    'byte',
    'addmod',
    'mulmod',
    'signextend',
    'keccak256',
    'pc',
    'pop',
    'mload',
    'mstore',
    'mstore8',
    'sload',
    'sstore',
    'msize',
    'gas',
    'address',
    'balance',
    'selfbalance',
    'caller',
    'callvalue',
    'calldataload',
    'calldatasize',
    'calldatacopy',
    'codesize',
    'codecopy',
    'extcodesize',
    'extcodecopy',
    'returndatasize',
    'returndatacopy',
    'extcodehash',
    'create',
    'create2',
    'call',
    'callcode',
    'delegatecall',
    'staticcall',
    'return',
    'revert',
    'selfdestruct',
    'invalid',
    'log0',
    'log1',
    'log2',
    'log3',
    'log4',
    'chainid',
    'origin',
    'gasprice',
    'blockhash',
    'coinbase',
    'timestamp',
    'number',
    'difficulty',
    'gaslimit'
    'datasize',
    'dataoffset',
    'datacopy',
]

unary_ops = {
    'not': UnaryOperationType.TILD,
    'iszero': UnaryOperationType.BANG,
}

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
    'shl': BinaryOperationType.LEFT_SHIFT,
    'shr': BinaryOperationType.RIGHT_SHIFT,
    'sar': BinaryOperationType.RIGHT_SHIFT,
}

class YulFunction(Expression):
    # Non standard handling of type(address). This function returns an undefined object
    # The type is dynamic
    # https://solidity.readthedocs.io/en/latest/units-and-global-variables.html#type-information
    # As a result, we set return_type during the Ir conversion

    def __init__(self, name):
        super(YulFunction, self).__init__()
        self._name = name
        self._return_type = []

    @property
    def name(self):
        return self._name

    @property
    def full_name(self):
        return self.name

    @property
    def return_type(self):
        return self._return_type

    @return_type.setter
    def return_type(self, r):
        self._return_type = r

    def __str__(self):
        return self._name

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)
