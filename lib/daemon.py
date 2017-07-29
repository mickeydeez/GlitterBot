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

    class LogHandler(object):

        def __init__(self):
            self.recent_logs = []

        def emit(self, record):
            try:
                if len(self.recent_logs) >= 10:
                    del(self.recent_logs[0])
                self.recent_logs.append(record)
            except (KeyboardInterrupt, SystemExit):
                raise


    def __init__(self, config_path, log=True):
        self.config_path = config_path
        self.client = Client(config_path, log=log)
        self.reload_config()
        self.tweets = self.load_tweets()
        self.running = True
        self.start_time = datetime.now()
        self.total_retweets = 0
        self.total_tweets = 0
        self.total_follows = 0
        self.total_favourites = 0
        self.uptime = ''
        self.last_tweet_user = ''
        self.last_tweet_text = ''
        self.log_handler = self.LogHandler()
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
        uptime_thread = Timer(
            2,
            self.track_uptime
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
            try:
                data = load(f.read())
            except:
                logging.info("Error in configuration syntax, keeping old values")
                return
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
            self.min_hour = data['minimum_hour'] or None
            self.max_hour = data['maximum_hour'] or None
        except KeyError:
            self.min_hour = None
            self.max_hour = None
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
            self.last_config_reload = datetime.now()

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
                            self.total_tweets += 1
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
                            retweeted = False
                            favourited = False
                            followed = False
                            try:
                                self.client.favourite(tweet)
                                self.total_favourites += 1
                                favourited = True
                                sleep(3)
                            except tweepy.TweepError as e:
                                sleep(3)
                                logging.info(e.reason)
                                sleep(3)
                            if self.follow_users:
                                if not tweet.user.following:
                                    try:
                                        self.client.follow(tweet.user)
                                        self.total_follows += 1
                                        follows = True
                                        sleep(3)
                                    except tweepy.TweepError as e:
                                        logging.info(e.reason)
                                        sleep(3)
                                else:
                                    logging.info("Already following the user")
                            try:
                                self.client.retweet(tweet)
                                self.total_retweets += 1
                                retweeted = True
                            except tweepy.TweepError as e:
                                logging.info(e.reason)
                                sleep(5)
                            self.log_handler.emit(
                                "Tweet by @%s: %s" % (
                                    tweet.user.screen_name,
                                    tweet.text
                                )
                            )
                            self.log_handler.emit(
                                "\tFavourited: %s" % favourited
                            )
                            self.log_handler.emit(
                                "\tFollowing: %s" % bool(tweet.user.following) or followed
                            )
                            self.log_handler.emit(
                                "\tRetweeted: %s" % retweeted
                            )
                            if retweeted:
                                sleep(self.retweet_sleep)
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
        if tweet.user.screen_name == self.client.name:
            return self.log_filtered("It's you!")
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
                        cmd = "str('%s').lower() in tweet.text.lower() or False" % (
                            item
                        )
                        status = eval(cmd)
                    else:
                        cmd = 'type(tweet.%s)' % value['tweet_suffix']
                        itype = eval(cmd)
                        if itype is str:
                            cmd = "tweet.%s.lower() == str('%s').lower() or False" % (
                                value['tweet_suffix'], item
                            )
                            status = eval(cmd)
                        elif itype is list:
                            cmd = "type(tweet.%s[0])" % value['tweet_suffix']
                            stype = eval(cmd)
                            if stype is dict:
                                cmd = "[ True for x in tweet.%s if str('%s').lower() in x['text'].lower() ]" % (
                                    value['tweet_suffix'], item
                                )
                            else:
                                cmd = "[ True for x in tweet.%s if str('%s').lower() in x.lower() ]" % (
                                    value['tweet_suffix'], item
                                )
                            try:
                                res = eval(cmd)
                            except Exception as e:
                                data = eval("tweet.%s" % value['tweet_suffix'])
                                print(data)
                                print(key)
                                print(item)
                                print(e)
                                raise
                            if len(res) >= 1:
                                status = True
                            else:
                                status = False
                    if status:
                        return self.log_filtered(key)
            else:
                pass
        return True

    def get_run_metrics(self):
        logging.info("[*] Uptime: %s" % self.uptime)
        logging.info("[*] Total Tweets: %s" % self.total_tweets)
        logging.info("[*] Total Retweets: %s" % self.total_retweets)
        logging.info("[*] Total Follows: %s" % self.total_follows)
        logging.info("[*] Total Favourites: %s" % self.total_favourites)
    
    def track_uptime(self):
        if self.running:
            now = datetime.now()
            uptime = now - self.start_time
            seconds = uptime.total_seconds()
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            if seconds == 0 or seconds > 1:
                second_string = 'seconds'
            else:
                second_string = 'second'
            if minutes == 0 or minutes > 1:
                minute_string = 'minutes'
            else:
                minute_string = 'minute'
            if hours == 0 or hours > 1:
                hour_string = 'hours'
            else:
                hour_string = 'hour'
            self.uptime = '%s %s, %s %s, %s %s' % (
                int(hours),
                hour_string,
                int(minutes),
                minute_string,
                int(seconds),
                second_string
            )
            uptime_thread = Timer(
                2,
                self.track_uptime
            ).start()


    def is_operating_time(self):
        if not self.min_hour or not self.max_hour:
            return True
        now = datetime.now()
        if now.hour < self.min_hour or now.hour > self.max_hour:
            logging.info("We are sleeping right now...")
            self.log_handler.emit("We are sleeping...")
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
        self.get_run_metrics()
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
