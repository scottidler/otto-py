#!/usr/bin/env python3

import os
import re
import sys
sys.dont_write_bytecode = True

DIR = os.path.abspath(os.path.dirname(__file__))
CWD = os.path.abspath(os.getcwd())
REL = os.path.relpath(DIR, CWD)

REAL_FILE = os.path.abspath(__file__)
REAL_NAME = os.path.basename(REAL_FILE)
REAL_PATH = os.path.dirname(REAL_FILE)
if os.path.islink(__file__):
    LINK_FILE = REAL_FILE; REAL_FILE = os.path.abspath(os.readlink(__file__))
    LINK_NAME = REAL_NAME; REAL_NAME = os.path.basename(REAL_FILE)
    LINK_PATH = REAL_PATH; REAL_PATH = os.path.dirname(REAL_FILE)

from argparse import ArgumentParser

OTTO_YML = os.environ.get('OTTO_YML', './otto.yml')

class Parser:
    def __init__(self):
        self.ottofile, self.args = Parser.divine_ottofile(sys.argv)

    def __repr__(self):
        return f'Parser(ottofile={self.ottofile}, args={self.args})'

    __str__ = __repr__

    @staticmethod
    def divine_ottofile(args):
        parser = Parser.otto_seed()
        ns, rem = parser.parse_known_args(args)
        return (ns.ottofile, rem)

    @staticmethod
    def otto_seed():
        parser = ArgumentParser(description='otto')
        parser.add_argument('-o', '--ottofile', 
            default=OTTO_YML,
            help='otto file')
        return parser

def main():
    parser = Parser()
    print(f'parser={parser}')

if __name__ == '__main__':
    main()

