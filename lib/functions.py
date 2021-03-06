#!/usr/bin/env python

from lib.client import Client
from lib.daemon import Daemon
from lib.crawler import Crawler
from lib.interface import CursesInterface
from time import sleep
from sys import exit
from threading import active_count
from os import path


def daemon_mode(config_path):
    try:
        twit = Daemon(config_path, log=False)
        twit.spawn_watchers()
        twit.spawn_tweet_thread()
        twit.spawn_retweet_thread()
        interface = CursesInterface(twit)
        interface.run()
        while active_count() > 0:
            try:
                sleep(1)
            except Exception as e:
                twit.log_handler.emit(e, rec_type='error')
                sleep(1)
    except KeyboardInterrupt:
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
