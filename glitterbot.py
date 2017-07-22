#!/usr/bin/env python

from lib.functions import daemon_mode, tweet_list, retweet
from argparse import ArgumentParser
from sys import argv, exit


def run():
    args = parse_args()
    args = sanitize_args(args)
    if args.action == 'daemon':
        daemon_mode(args.config_path)
        exit()
    if args.tweet_list:
        tweet_list(args)
    if args.retweet_search:
        retweet(args)
    exit()


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
        help='Run tweet/retweet daemon. Overrides all other options'
    )
    parser.add_argument(
        '-s',
        '--sleep',
        action='store',
        dest='int_sleep',
        help="Sleep time between CLI actions. Default is 10 seconds."
    )
    parser.add_argument(
        '-tL',
        '--tweet-list',
        action='store',
        dest='tweet_list',
        help="A text file of tweets to send out."
    )
    parser.add_argument(
        '-rT',
        '--retweet',
        action='store',
        dest='retweet_search',
        help="Hashtag or user to retweet. Will be prompted before action."
    )
    if len(argv) == 1:
        parser.print_help()
        exit(1)
    args, unknown = parser.parse_known_args()
    return args


def sanitize_args(args):
    if not args.config_path:
        args.config_path = 'config.yml'
    if not args.int_sleep:
        args.int_sleep = 10
    return args


if __name__ == '__main__':
    run()
