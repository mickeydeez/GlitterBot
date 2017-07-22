#!/usr/bin/env python

from lib.client import Tweeter
from time import sleep
from sys import exit
from threading import active_count
from os import path
from signal import SIGTERM, signal


def daemon_mode(config_path):
    twit = Tweeter(config_path)
    twit.spawn_watchers()
    twit.spawn_tweet_thread()
    twit.spawn_retweet_thread()
    try:
        while active_count() > 0:
            sleep(0.1)
    except KeyboardInterrupt:
        print("[*] Stopping threads. This may take a while depending on sleep times.")
        twit.stop_threads()
        exit()


def tweet_list(args):
    if path.isfile(args.tweet_list):
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


def tweet(args):
    twit = Tweeter(args.config_path)
    stripped = args.tweet.strip()
    print("[*] Tweeting: %s" % stripped)
    twit.tweet(stripped)
    

def retweet(args):
    twit = Tweeter(args.config_path)
    twit.retweet(args.retweet_search)
