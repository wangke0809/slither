import os, sys
import argparse
from slither import Slither
from slither.utils.colors import red
import logging
from .slither_evm import slither_evm
from crytic_compile import cryticparser

logging.basicConfig()
logging.getLogger("Slither").setLevel(logging.INFO)

def parse_args():
    """
    Parse the underlying arguments for the program.
    :return: Returns the arguments for the program.
    """
    parser = argparse.ArgumentParser(description='slither-evm',
                                     usage='slither-evm filename')

    parser.add_argument('filename', help='The filename of the Solidity contract or Truffle directory to analyze.')
    parser.add_argument('--verbose-test', '-v', help='verbose mode output for testing',action='store_true',default=False)
    parser.add_argument('--verbose-json', '-j', help='verbose json output',action='store_true',default=False)
    parser.add_argument('--version',
                        help='displays the current version',
                        version='0.1.0',
                        action='version')
    
    cryticparser.init(parser) 
  
    if len(sys.argv) == 1: 
        parser.print_help(sys.stderr) 
        sys.exit(1)
     
    return parser.parse_args()


def main():
    # ------------------------------
    #       Usage: python3 -m slither_evm filename
    #       Example: python3 -m slither_evm contract.sol
    # ------------------------------
    # Parse all arguments
    args = parse_args()

    # Perform slither analysis on the given filename
    slither = Slither(args.filename, **vars(args))

    #  Annotate the input files (Solidity <-> EVM) based on slither analysis
    slither_evm(args, slither)
if __name__ == '__main__':
    main()
