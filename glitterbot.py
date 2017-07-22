#!/usr/bin/env python

from lib.functions import daemon_mode, tweet_list, retweet, tweet
from lib.parser import parse_args, sanitize_args
from sys import exit


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
    if args.tweet:
        tweet(args)
    exit()


if __name__ == '__main__':
    run()
