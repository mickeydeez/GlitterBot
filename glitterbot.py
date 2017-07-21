#!/usr/bin/env python

from lib.functions import daemon_mode
from argparse import ArgumentParser
from sys import argv, exit


def run():
    args, unknown, config_path = parse_args()
    if args.action == 'daemon':
        daemon_mode(config_path)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        action='store',
        dest='config_path',
        help="Path to configuration file. Default is ./config.yml"
    )
    parser.add_argument(
        '-d',
        '--daemon',
        action='store_const',
        const='daemon',
        dest='action',
        help='Run tweet/retweet daemon'
    )
    if len(argv) == 1:
        parser.print_help()
        exit(1)
    args, unknown = parser.parse_known_args()
    if not args.config_path:
        config_path = 'config.yml'
    else:
        config_path = args.config_path
    return args, unknown, config_path


if __name__ == '__main__':
    run()
