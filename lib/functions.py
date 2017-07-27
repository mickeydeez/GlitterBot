#!/usr/bin/env python

from lib.client import Client
from lib.daemon import Daemon
from lib.crawler import Crawler
from time import sleep
from sys import exit
from threading import active_count
from os import path


def daemon_mode(config_path):
    twit = Daemon(config_path)
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
        twit = Client(args.config_path, log=False)
        for tweet in tweets:
            stripped = tweet.strip()
            print("[*] Tweeting: %s" % stripped)
            twit.tweet(stripped)
            print("[*] Sleeping for %s seconds" % str(args.int_sleep))
            sleep(args.int_sleep)

    else:
        exit("No such file: %s" % args.tweet_list)


def tweet(args):
    twit = Client(args.config_path, log=True)
    stripped = args.tweet.strip()
    print("[*] Tweeting: %s" % stripped)
    twit.tweet(stripped)
    

def retweet(args):
    twit = Client(args.config_path, log=True)
    twit.retweet_loop(args.retweet_search)


def get_my_stats(args):
    twit = Client(args.config_path, log=True)
    twit.dump_stats()


def user_lookup(args):
    twit = Client(args.config_path, log=True)
    twit.dump_stats(user=args.user_lookup)
    twit.extended_stats(user=args.user_lookup)


def enumerate_twit(args):
    twit = Crawler(args.config_path, args.enum_search)
