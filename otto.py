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

OTTO_YML = os.environ.get('OTTO_YML', './otto.yml')

class Parser:
    def __init__(self):
        self.prog, self.args, self.ottofile = Parser.divine_ottofile(sys.argv)

    def __repr__(self):
        return f'Parser(prog={self.prog}, args={self.args}, ottofile={self.ottofile})'

    __str__ = __repr__

    @staticmethod
    def divine_ottofile(args):
        prog, *args = args
        parser = Parser.otto_seed('otto', True)
        ns, rem = parser.parse_known_args(args)
        return (prog, rem, ns.ottofile)

    @staticmethod
    def otto_seed(prog: str, nerfed: bool = False):
        parser = ArgumentParser(
            prog=prog,
            add_help=not nerfed)
        parser.add_argument(
            '-o', '--ottofile',
            default=OTTO_YML,
            help='otto file')
        return parser

    @staticmethod
    def load_yaml(filename):
        with open(filename, 'r') as f:
            return Addict(safe_load(f))

    @staticmethod
    def task_to_command(task):
        parser = ArgumentParser(task.name)
        for name, param in task.params.items():
            short, long_ = Parser.name_to_short_long(name)
            parser.add_argument(
                short, long_,
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

    @staticmethod
    def name_to_short_long(name):
        parts = name.split('|')
        if len(parts) == 2:
            return sorted(parts, key=len)
        if len(parts) == 1:
            if '--' in parts[0]:
                return None, parts[0]
            else:
                return parts[0], None
        raise ValueError(f'invalid name {name}')

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
        otto = Parser.otto_seed(self.prog)
        if os.path.isfile(self.ottofile):
            spec = Parser.load_yaml(self.ottofile)
            task_names = spec.otto.tasks.keys()
            if task_names:
                partitions = self.partitions(task_names)
                if partitions:
                    print(f'partitions={partitions}')
                    for partition in partitions:
                        name, *args = partition
                        task = spec.otto.tasks[name]
                        command = Parser.task_to_command(task)
                        print(f'name={name} args={args}')
                        ns = command.parse_args(args)
                        print(f'ns={ns}')
                        nss.append(ns)
                else:
                    print(f'not partitions found in args={self.args}')
                    otto1 = Parser.otto_with_subcommands(otto, spec.otto.tasks)
                    ns = otto1.parse_args(self.args)
                    nss.append(ns)
            else:
                print(f'no tasks in {self.ottofile}')
                print(f'spec.otto={spec.otto}')

                otto2 = ArgumentParser('otto')
                for name, param in spec.otto.params.items():
                    print(f'name={name} param={param}')
                    short, long_ = Parser.name_to_short_long(name)
                    print(f'short={short} long={long_}')
                    if short and long_:
                        otto2.add_argument(
                            short, long_,
                            default=param.default,
                            help=param.help)
                    else:
                        otto2.add_argument(
                            name,
                            default=param.default,
                            help=param.help)
                ns = otto2.parse_args(self.args)
                nss.append(ns)
        else:
            print(f'no such file {self.ottofile}')
            otto.epilog = f'no such file {self.ottofile}'
            ns = otto.parse_args(['--help'])
            nss.append(ns)
        return nss

def main():
    parser = Parser()
    print(f'parser={parser}')
    nss = parser.parse()
    print(f'nss={nss}')

if __name__ == '__main__':
    main()
