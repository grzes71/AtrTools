"""Set of Atari development conversion tools.
"""
import argparse 
import logging

from atrtools import imgconv
from atrtools import sapconv

VERSION = '0.1.0'

def log():
    return logging.getLogger(__name__)

def run_sapconv(args):
    "Run sapconv with arguments"
    log().info('Running sapconv tool')
    sapconv.process(args)

def run_imgconv(args):
    "Run imgconv with arguments"
    log().info('Running imgconv tool')
    imgconv.process(args)

def parse_args():
    "Parse command-line argumenmts"
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(VERSION), 
                                help='Print version and quit')

    parser = argparse.ArgumentParser(description='Atari Development Support Tools')
    parser.set_defaults(func=lambda x: parser.print_help())

    subparsers = parser.add_subparsers(help='Select tool')
    
    parser_sapconv = subparsers.add_parser('sapconv', help='SAP music converter', parents=[parent_parser])
    parser_imgconv = subparsers.add_parser('imgconv', help='Gif image converter', parents=[parent_parser])
    
    parser_sapconv.set_defaults(func=run_sapconv)
    parser_imgconv.set_defaults(func=run_imgconv)

    sapconv.add_parser_args(parser_sapconv)
    imgconv.add_parser_args(parser_imgconv)

    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args)

def main():
    parse_args()

if __name__ == '__main__':
    main()