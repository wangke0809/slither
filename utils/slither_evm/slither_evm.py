import sys, re, logging, subprocess
import sha3
from collections import defaultdict
from slither.utils.colors import red, yellow, set_colorization_enabled
from evm_cfg_builder.cfg import CFG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Slither.EVM')
set_colorization_enabled(True)

def slither_evm(args, slither):
    print_evm_source_mapping_functions(slither)

def print_evm_cfg(slither):
    for contract in slither.contracts:
        contract_runtime_bytecode = slither.crytic_compile.bytecode_runtime(contract.name)
        cfg = CFG(contract_runtime_bytecode)
        for basic_block in cfg.basic_blocks:
            print('{} -> {}'.format(basic_block, sorted(basic_block.all_outgoing_basic_blocks, key=lambda x:x.start.pc)))

def print_evm_functions(slither):
    for contract in slither.contracts:
        print('Contract {}'.format(contract.name))
        contract_runtime_bytecode = slither.crytic_compile.bytecode_runtime(contract.name)
        cfg = CFG(contract_runtime_bytecode)
        for function in sorted(cfg.functions, key=lambda x: x.start_addr):
            print('Function {}'.format(function.name))
            # Each function may have a list of attributes
            # An attribute can be:
            # - payable
            # - view
            # - pure
            if sorted(function.attributes):
                print('\tAttributes:')
                for attr in function.attributes:
                    print('\t\t-{}'.format(attr))

            print('\n\tBasic Blocks:')
            for basic_block in sorted(function.basic_blocks, key=lambda x:x.start.pc):
                # Each basic block has a start and end instruction
                # instructions are pyevmasm.Instruction objects
                print('\t- @{:x}-{:x}'.format(basic_block.start.pc,
                                              basic_block.end.pc))

                print('\t\tInstructions:')
                for ins in basic_block.instructions:
                    print('\t\t- {}'.format(ins.name))

                # Each Basic block has a list of incoming and outgoing basic blocks
                # A basic block can be shared by different functions
                # And the list of incoming/outgoing basic blocks depends of the function
                # incoming_basic_blocks(function_key) returns the list for the given function 
                print('\t\tIncoming basic_block:')
                for incoming_bb in sorted(basic_block.incoming_basic_blocks(function.key), key=lambda x:x.start.pc):
                    print('\t\t- {}'.format(incoming_bb))

                print('\t\tOutgoing basic_block:')
                for outgoing_bb in sorted(basic_block.outgoing_basic_blocks(function.key), key=lambda x:x.start.pc):
                    print('\t\t- {}'.format(outgoing_bb))

def print_evm_source_mapping_functions(slither):
    for contract in slither.contracts:
        print('Contract {}'.format(contract.name))
        contract_runtime_bytecode = slither.crytic_compile.bytecode_runtime(contract.name)
        cfg = CFG(contract_runtime_bytecode)
        for function in contract.functions:
            print('Function {}'.format(function.name))
            print('Source Mapping start:{} end:{}'.format(function.source_mapping['start'],
                                                          function.source_mapping['start'] +
                                                          function.source_mapping['length']))
            # Get first four bytes of function singature's keccak-256 hash used as function selector
            function_hash = "0x" + get_function_hash(function.full_name)[:8]
            function_evm = get_function_evm(cfg, function.name, function_hash)
            if function_evm == "None":
                # Constructors
                continue
            if sorted(function_evm.attributes):
                print('\tAttributes:')
                for attr in function_evm.attributes:
                    print('\t\t-{}'.format(attr))
            print('\n\tBasic Blocks:')
            for basic_block in sorted(function_evm.basic_blocks, key=lambda x:x.start.pc):
                # Each basic block has a start and end instruction
                # instructions are pyevmasm.Instruction objects
                print('\t- @{:x}-{:x}'.format(basic_block.start.pc,
                                              basic_block.end.pc))
                print('\t\tInstructions:')
                for ins in basic_block.instructions:
                    print('\t\t- {}'.format(ins.name))
                # Each Basic block has a list of incoming and outgoing basic blocks
                # A basic block can be shared by different function_evms
                # And the list of incoming/outgoing basic blocks depends of the function_evm
                # incoming_basic_blocks(function_evm_key) returns the list for the given function_evm 
                print('\t\tIncoming basic_block:')
                for incoming_bb in sorted(basic_block.incoming_basic_blocks(function_evm.key), key=lambda x:x.start.pc):
                    print('\t\t- {}'.format(incoming_bb))
                print('\t\tOutgoing basic_block:')
                for outgoing_bb in sorted(basic_block.outgoing_basic_blocks(function_evm.key), key=lambda x:x.start.pc):
                    print('\t\t- {}'.format(outgoing_bb))

def get_function_hash(function_signature):
    hash = sha3.keccak_256()
    hash.update(function_signature.encode('utf-8'))
    return hash.hexdigest()

def get_function_evm(cfg, function_name, function_hash):
    for function_evm in cfg.functions:
        if function_evm.name[:2] == "0x" and function_evm.name == function_hash:
            return function_evm
        elif function_evm.name[:2] != "0x" and function_evm.name.split('(')[0] == function_name:
            return function_evm
    return "None"
