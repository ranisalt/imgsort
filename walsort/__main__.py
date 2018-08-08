#!/usr/bin/env python3
import argparse
import logging
import os
import shutil

from . import sort


def dedup_wrapper(args):
    from . import dedup
    return dedup.main(args)


parser = argparse.ArgumentParser(
    description='Automatic wallpaper sorter by image dimensions')

parser.add_argument('-d', '--debug', action='store_const', const=logging.DEBUG,
                    default=logging.INFO)
parser.add_argument('-n', '--dry-run', action='store_true')

subparsers = parser.add_subparsers(title='subcommands')

dedup_parser = subparsers.add_parser('dedup', aliases=['d'])
dedup_parser.add_argument('-t', '--threshold', type=float, default=0.3,
                          metavar='T', help='similarity threshold')
dedup_parser.add_argument('images', nargs='*', type=os.path.abspath)
dedup_parser.set_defaults(func=dedup_wrapper)

sort_parser = subparsers.add_parser('sort', aliases=['s'])
sort_parser.add_argument('-m', '--move', action='store_const',
                         const=shutil.move, default=shutil.copyfile)
sort_parser.add_argument('images', nargs='*', type=os.path.abspath)
sort_parser.add_argument('output', type=os.path.abspath)
sort_parser.set_defaults(func=sort.main)

# TODO: watch folder

args = parser.parse_args()

# Setup logging facility
logger = logging.getLogger('walsort')
logger.setLevel(args.debug)
ch = logging.StreamHandler()
ch.setLevel(args.debug)
fmt = logging.Formatter('[%(levelname)s - %(filename)s:%(lineno)d] - %(message)s')
ch.setFormatter(fmt)
logger.addHandler(ch)

args.func(args)
