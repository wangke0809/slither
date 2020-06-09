from slither.core.expressions import BinaryOperationType, UnaryOperationType

# taken from https://github.com/ethereum/solidity/blob/356cc91084114f840da66804b2a9fc1ac2846cff/libevmasm/Instruction.cpp#L180
builtins = [
    "STOP",
    "ADD",
    "SUB",
    "MUL",
    "DIV",
    "SDIV",
    "MOD",
    "SMOD",
    "EXP",
    "NOT",
    "LT",
    "GT",
    "SLT",
    "SGT",
    "EQ",
    "ISZERO",
    "AND",
    "OR",
    "XOR",
    "BYTE",
    "SHL",
    "SHR",
    "SAR",
    "ADDMOD",
    "MULMOD",
    "SIGNEXTEND",
    "KECCAK256",
    "ADDRESS",
    "BALANCE",
    "ORIGIN",
    "CALLER",
    "CALLVALUE",
    "CALLDATALOAD",
    "CALLDATASIZE",
    "CALLDATACOPY",
    "CODESIZE",
    "CODECOPY",
    "GASPRICE",
    "EXTCODESIZE",
    "EXTCODECOPY",
    "RETURNDATASIZE",
    "RETURNDATACOPY",
    "EXTCODEHASH",
    "BLOCKHASH",
    "COINBASE",
    "TIMESTAMP",
    "NUMBER",
    "DIFFICULTY",
    "GASLIMIT",
    "CHAINID",
    "SELFBALANCE",
    "POP",
    "MLOAD",
    "MSTORE",
    "MSTORE8",
    "SLOAD",
    "SSTORE",
    "JUMP",
    "JUMPI",
    "PC",
    "MSIZE",
    "GAS",
    "JUMPDEST",
    "PUSH1",
    "PUSH2",
    "PUSH3",
    "PUSH4",
    "PUSH5",
    "PUSH6",
    "PUSH7",
    "PUSH8",
    "PUSH9",
    "PUSH10",
    "PUSH11",
    "PUSH12",
    "PUSH13",
    "PUSH14",
    "PUSH15",
    "PUSH16",
    "PUSH17",
    "PUSH18",
    "PUSH19",
    "PUSH20",
    "PUSH21",
    "PUSH22",
    "PUSH23",
    "PUSH24",
    "PUSH25",
    "PUSH26",
    "PUSH27",
    "PUSH28",
    "PUSH29",
    "PUSH30",
    "PUSH31",
    "PUSH32",
    "DUP1",
    "DUP2",
    "DUP3",
    "DUP4",
    "DUP5",
    "DUP6",
    "DUP7",
    "DUP8",
    "DUP9",
    "DUP10",
    "DUP11",
    "DUP12",
    "DUP13",
    "DUP14",
    "DUP15",
    "DUP16",
    "SWAP1",
    "SWAP2",
    "SWAP3",
    "SWAP4",
    "SWAP5",
    "SWAP6",
    "SWAP7",
    "SWAP8",
    "SWAP9",
    "SWAP10",
    "SWAP11",
    "SWAP12",
    "SWAP13",
    "SWAP14",
    "SWAP15",
    "SWAP16",
    "LOG0",
    "LOG1",
    "LOG2",
    "LOG3",
    "LOG4",
    "CREATE",
    "CALL",
    "CALLCODE",
    "STATICCALL",
    "RETURN",
    "DELEGATECALL",
    "CREATE2",
    "REVERT",
    "INVALID",
    "SELFDESTRUCT",
]

builtins = [x.lower() for x in builtins if not (
        x.startswith("PUSH") or
        x.startswith("SWAP") or
        x.startswith("DUP") or
        x == "JUMP" or
        x == "JUMPI" or
        x == "JUMPDEST"
)] + [
               "datasize",
               "dataoffset",
               "datacopy",
               "setimmutable",
               "loadimmutable",
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


class YulBuiltin:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name
