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
from ruamel.yaml import safe_load
from addict import Addict
from leatherman.repr import __repr__

OTTO_YML = os.environ.get('OTTO_YML', './otto.yml')

OTTO_FILES = [
    'otto.yml',
    'otto.yaml',
    '.otto.yml',
    '.otto.yaml',
]

class MultipleOttofilesFoundError(Exception):
    def __init__(self, ottofiles, path):
        msg = f'error: multiple ottofiles={ottofiles} in path={path}'
        super().__init__(msg)

class Parser:
    def __init__(self):
        self.cwd = os.getcwd()
        self.prog, *self.args = sys.argv
        self.prog = os.path.basename(self.prog)
        self.ottofile = self.divine_ottofile()

    __str__ = __repr__

    def divine_ottofile(self):
        parser = Parser.otto_seed('otto', True)
        ns, rem = parser.parse_known_args(self.args)
        self.args = rem
        if ns.ottofile is None:
            print('ottofile is None')
            ns.ottofile = Parser.find_ottofile(self.cwd)
        return ns.ottofile

    @staticmethod
    def find_ottofile(path):
        path = os.path.abspath(path)
        if path == '/':
            return None
        _, _, files = next(os.walk(path))
        intersection = list(set(files) & set(OTTO_FILES))
        if len(intersection) >= 2:
            raise MultipleOttofilesFoundError(intersection, path)
        elif len(intersection) == 1:
            return os.path.join(path, intersection[0])
        return Parser.find_ottofile(os.path.dirname(path))

    @staticmethod
    def otto_seed(prog: str, nerfed: bool = False):
        parser = ArgumentParser(
            prog=prog,
            add_help=not nerfed)
        parser.add_argument(
            '-o', '--ottofile',
            metavar='FILE',
            default=None,
            help='default="%(default)s"; path to ottofile')
        return parser

    @staticmethod
    def load_yaml(filename):
        with open(filename, 'r') as f:
            return Addict(safe_load(f))

    @staticmethod
    def task_to_parser(task):
        parser = ArgumentParser(task.name)
        for name, param in task.params.items():
            # short, long_ = Parser.name_to_short_long(name)
            parser.add_argument(
                # short, long_,
                *name.split('|'),
                default=param.default,
                help=param.help)
        return parser

    @staticmethod
    def otto_with_subcommands(parser, tasks):
        subparsers = parser.add_subparsers(dest='task')
        for name, task in tasks.items():
            subparser = subparsers.add_parser(
                name,
                help=task.help)
        return parser

#    @staticmethod
#    def name_to_short_long(name):
#        parts = name.split('|')
#        if len(parts) == 2:
#            return sorted(parts, key=len)
#        if len(parts) == 1:
#            if '--' in parts[0]:
#                return None, parts[0]
#            else:
#                return parts[0], None
#        raise ValueError(f'invalid name {name}')

    def indices(self, task_names):
        indices = []
        for (index, arg) in enumerate(self.args):
            if arg in task_names:
                indices.append(index)
        return indices

    def partitions(self, task_names):
        partitions = []
        end = len(self.args)
        indices = self.indices(task_names)
        indices.reverse()
        for index in indices:
            partitions.insert(0, self.args[index:end])
            end = index
        return partitions

    def parse(self):
        nss = []
        otto_parser = Parser.otto_seed(self.prog)
        ## test if ottofile exists
        if self.ottofile and os.path.isfile(self.ottofile):
            ## ottofile exists
            spec = Parser.load_yaml(self.ottofile)
            task_names = spec.otto.tasks.keys()
            if task_names:
                ## ottofile has tasks
                partitions = self.partitions(task_names)
                if partitions:
                    ## partitions exist
                    print(f'partitions={partitions}')
                    for partition in partitions:
                        name, *args = partition
                        task = spec.otto.tasks[name]
                        task_parser = Parser.task_to_parser(task)
                        ns = task_parser.parse_args(args)
                        nss.append((name,ns))
                else:
                    ## no partitions
                    print(f'no partitions found in args={self.args}')
                    otto_parser = Parser.otto_with_subcommands(otto_parser, spec.otto.tasks)
                    ns = otto_parser.parse_args(self.args)
                    nss.append(('otto', ns))
            else:
                ## ottofile has no tasks
                for name, param in spec.otto.params.items():
                    otto_parser.add_argument(
                        *name.split('|'),
                        default=param.default,
                        help=param.help)
                ns = otto_parser.parse_args(self.args)
                nss.append(('otto', ns))
        else:
            ## ottofile does not exist
            otto_parser.epilog = f'no such ottofile="{self.ottofile}"'
            ns = otto_parser.parse_args(['--help'])
            nss.append(('otto', ns))
        return nss

def main():
    parser = Parser()
    print(f'parser={parser}')
    nss = parser.parse()
    print(f'nss={nss}')

if __name__ == '__main__':
    main()
