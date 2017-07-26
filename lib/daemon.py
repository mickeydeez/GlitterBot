#!/usr/bin/env python3

from lib.exceptions import BadConfiguration, InvalidParameter
from lib.client import Client
from signal import signal, SIGUSR1, SIGUSR2
from datetime import datetime
from time import sleep
from threading import Thread, Timer
from random import choice
from yaml import load
from os import path

import tweepy
import logging


class Daemon(object):

    def __init__(self, config_path, log=True):
        self.config_path = config_path
        self.client = Client(config_path, log=log)
        self.reload_config()
        self.tweets = self.load_tweets()
        self.running = True
        signal(SIGUSR1, self.catch_signal)
        if log:
            logging.basicConfig(level=self.client.log_level,
                format='[%(levelname)s] (%(threadName)-10s) %(message)s'
            )


    def spawn_watchers(self):
        Timer(
            self.config_reload_time,
            self.config_watcher
        ).start()
        Timer(
            self.tweets_reload_time,
            self.tweet_watcher
        ).start()


    def spawn_tweet_thread(self):
        tweet_thread = Thread(
            name = 'tweeter',
            target = self.async_tweet
        )
        tweet_thread.setDaemon(True)
        tweet_thread.start()
    
    
    def spawn_retweet_thread(self):
        retweet_thread = Thread(
            name = 'retweeter',
            target = self.async_retweet
        )
        retweet_thread.setDaemon(True)
	retweet_thread.start()


    def reload_config(self):
        self.filters = {
            'following_limit': {'tweet_suffix': 'author.friends_count', 'value': 0},
            'favourites_limit': {'tweet_suffix': 'author.favourites_count', 'value': 0},
            'followers_limit': {'tweet_suffix': 'author.followers_count', 'value': 0},
            'statuses_limit': {'tweet_suffix': 'author.statuses_count', 'value': 0},
            'retweeted_limit': {'tweet_suffix': 'retweet_count', 'value': 0},
            'blocked_hashtags': {'tweet_suffix': "entities['hashtags']", 'value': []},
            'blocked_user_mentions': {'tweet_suffix': "entities['user_mentions']", 'value': []},
            'blocked_users': {'tweet_suffix': 'user.screen_name', 'value': []},
            'trigger_phrases': {'tweet_suffix': 'n/a', 'value': []}

        }
        with open(self.config_path, 'r') as f:
            data = load(f.read())
        if not isinstance(data['watched_hashtags'], list):
            raise BadConfiguration
        else:
            self.watched_hashtags = data['watched_hashtags'] or []
        try:
            if path.isfile(data['tweets_path']):
                self.tweets_path = data['tweets_path']
            else:
                raise BadConfiguration
        except:
            self.tweets_path = None
        try:
            self.min_hour = data['minimum_hour']
            self.max_hour = data['maximum_hour']
        except KeyError:
            self.mix_hour = 10
            self.max_hour = 22
        try:
            self.follow_users = bool(data['follow_users']) or False
        except KeyError:
            self.follow_users = False
        try:
            self.retweet_sleep = int(data['retweet_sleep']) or 300
        except KeyError:
            self.retweet_sleep = 300
        try:
            self.tweet_sleep = int(data['tweet_sleep']) or 1200
        except KeyError:
            self.tweet_sleep = 1200
        try:
            self.config_reload_time = int(data['config_reload_time']) or 30
        except KeyError:
            self.config_reload_time = 30
        try:
            self.tweets_reload_time = int(data['tweets_reload_time']) or 30
        except KeyError:
            self.tweets_reload_time = 30
        for key, value in self.filters.iteritems():
            try:
                config = data[key]
                if isinstance(config, type(value['value'])):
                    if isinstance(config, int):
                        cmd = "self.filters['%s']['value'] = int(%s)" % (key, config)
                        exec(cmd)
                    elif isinstance(config, list):
                        cmd = "self.filters['%s']['value'] = '%s'.split(':')" % (
                            key, ':'.join(config)
                        )
                        exec(cmd)
                else:
                    logging.info("Unexpected data type for %s. Using default %s" % (
                        key, value
                    ))
            except KeyError:
                pass

    def async_tweet(self):
        while True:
            if not self.running:
                break
            if self.is_operating_time():
                try:
                    tweet = choice(self.tweets)
                except:
                    tweet = None
                if tweet:
                    try:
                        # need moar white space!
                        for i in range(0,5):
                            logging.debug('----------------------------------')
                        logging.info(tweet)
                        if tweet != '\n':
                            self.client.tweet(tweet)
                            self.update_tweets(tweet)
                            sleep(self.tweet_sleep)
                        else:
                            self.update_tweets(tweet)
                    except tweepy.TweepError as e:
                        logging.info(e.reason)
                        sleep(300)
                else:
                    logging.info("No more tweets...")
                    sleep(300)
            else:
                sleep(60)


    def async_retweet(self):
        while True:
            if not self.running:
                break
            try:
                if self.is_operating_time():
                    tag = choice(self.watched_hashtags)
                    for tweet in self.client.search(tag):
                        # need moar white space!
                        for i in range(0,5):
                            logging.debug('----------------------------------')
                        logging.info('\nTweet by: @' + tweet.user.screen_name)
                        logging.info(tweet.text)
                        if self.is_worth_while_tweet(tweet):
                            try:
                                self.client.favourite(tweet)
                            except tweepy.TweepError as e:
                                sleep(3)
                                logging.info(e.reason)
                                sleep(3)
                            if self.follow_users:
                                if not tweet.user.following:
                                    try:
                                        self.client.follow(tweet.user)
                                        sleep(3)
                                    except tweepy.TweepError as e:
                                        logging.info(e.reason)
                                        sleep(3)
                            try:
                                self.client.retweet(tweet)
                                sleep(self.retweet_sleep)
                            except tweepy.TweepError as e:
                                logging.info(e.reason)
                                sleep(5)
                            break
                    else:
                        continue
                else:
                    sleep(60)
                    continue
            except StopIteration:
                logging.debug("Hit query end")
                sleep(30)
                continue


    def is_worth_while_tweet(self, tweet):
        self.client.dump_tweet_stats(tweet)
        for key, value in self.filters.iteritems():
            if isinstance(value['value'], int):
                cmd = "tweet.%s < int(%s) or False" % (
                    value['tweet_suffix'], value['value']
                )
                if eval(cmd):
                    return self.log_filtered(key)
            elif isinstance(value['value'], list):
                for item in value['value']:
                    if key == 'trigger_phrases':
                        cmd = "str('%s') in tweet.text or False" % (
                            item
                        )
                    else:
                        cmd = "tweet.%s == str('%s') or False" % (
                            value['tweet_suffix'], item
                        )
                    if eval(cmd):
                        return self.log_filtered(key)
            else:
                pass
        return True


    def is_operating_time(self):
        if not self.min_hour or not self.max_hour:
            return True
        now = datetime.now()
        if now.hour < self.min_hour or now.hour > self.max_hour:
            logging.info("We are sleeping right now...")
            return False
        else:
            return True


    def log_filtered(self, ftype):
        logging.info("Failed to meet %s Filter" % ftype)
        return False


    def update_tweets(self, tweet):
        self.tweets.remove(tweet)
        with open(self.tweets_path, 'w') as f:
            f.writelines(self.tweets)


    def load_tweets(self):
        try:
            with open(self.tweets_path, 'r') as f:
                return f.readlines()
        except:
            return []


    def stop_threads(self):
        self.running = False


    def catch_signal(self, signum, frame):
        logging.info("[*] Caught signal. Dumping stats...")
        self.client.dump_stats()


    def config_watcher(self):
        if self.running:
            self.reload_config()
            logging.info("Configuration reloaded")
            Timer(
                self.config_reload_time,
                self.config_watcher
            ).start()


    def tweet_watcher(self):
        if self.running:
            self.tweets = self.load_tweets()
            logging.info("Tweets reloaded")
            Timer(
                self.tweets_reload_time,
                self.tweet_watcher
            ).start()
