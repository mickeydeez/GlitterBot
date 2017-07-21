#!/usr/bin/env python

from lib.client import Tweeter
from time import sleep
from sys import exit
import threading
import os


def daemon_mode(config_path):
    twit = Tweeter(config_path)
    twit.spawn_watchers()
    twit.spawn_tweet_thread()
    twit.spawn_retweet_thread()
    while threading.active_count() > 0:
        sleep(1)


def tweet_list(args):
    if os.path.isfile(args.tweet_list):
        with open(args.tweet_list, 'r') as f:
            tweets = f.readlines()
        twit = Tweeter(args.config_path)
        for tweet in tweets:
            stripped = tweet.strip()
            print("[*] Tweeting: %s" % stripped)
            twit.tweet(stripped)
            print("[*] Sleeping for %s seconds" % str(args.int_sleep))
            sleep(args.int_sleep)

    else:
        exit("No such file: %s" % args.tweet_list)
