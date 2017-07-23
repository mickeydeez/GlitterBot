#!/usr/bin/env python3

from lib.exceptions import BadConfiguration, InvalidParameter
from signal import signal, SIGUSR1, SIGUSR2
from datetime import datetime
from time import sleep
from threading import Thread, Timer
from random import choice
from yaml import load
from os import path

import tweepy
import logging


DEFAULT_LOG_LEVEL = logging.INFO


class Tweeter(object):

    def __init__(self, config_path, log=True):
        self.config_path = config_path
        self.reload_config()
        self.tweets = self.load_tweets()
        if log:
            logging.basicConfig(level=self.log_level,
                format='[%(levelname)s] (%(threadName)-10s) %(message)s'
            )
        self.api = self.auth()
        self.running = True
        signal(SIGUSR1, self.dump_stats)


    def catch_signal(self, signum, frame):
        print("[*] Caught signal. Dumping stats...")
        self.dump_stats()


    def dump_stats(self, user=None):
        if not user:
            data = self.api.me()
        else:
            if isinstance(user, str):
                data = self.api.get_user('%s' % str(user.replace('@', '')))
            else:
                raise InvalidParameter
        print("[*] Username: @%s" % data.screen_name)
        print("[*] Name: %s" % data.name)
        print("[*] Favourites: %s" % str(data.favourites_count))
        print("[*] Followers: %s" % str(data.followers_count))
        print("[*] Friends: %s" % str(data.friends_count))
        print("[*] Listed: %s" % str(data.listed_count))


    def extended_stats(self, user=None):
        if not user:
            data = self.api.me()
        else:
            if isinstance(user, str):
                data = self.api.get_user('%s' % str(user.replace('@', '')))
            else:
                raise InvalidParameter
        print("[*] Created: %s" % data.created_at)
        print("[*] Description: %s" % data.description)
        print("[*] Last update: %s" % data.status.created_at)
        hashtags = ' '.join(
            [ "#%s" % x['text'] for x in \
             data.status.entities['hashtags']]
        )
        mentions = ' '.join(
            [ "@%s" % x['screen_name'] for x in \
                data.status.entities['user_mentions']]
        )
        print("[*] \tUser Mentions: %s" % mentions)
        print("[*] \tHashtags: %s" % hashtags)
        if "RT @" in data.status.text:
            print("[*] \tRetweet Text: %s" % data.status.text)
        else:
            print("[*] \tTweet Text: %s" % data.status.text)
        print('[*] \tRetweet Count: %s' % str(data.status.retweet_count))


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
        with open(self.config_path, 'r') as f:
            data = load(f.read())
        if not isinstance(data['watched_hashtags'], list):
            raise BadConfiguration
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
            self.set_logging(data['log_level'])
        except KeyError:
            self.log_level = DEFAULT_LOG_LEVEL
        except:
            raise BadConfiguration
        try:
            self.consumer_key = data['consumer_key']
            self.consumer_secret = data['consumer_secret']
            self.access_token = data['access_token']
            self.access_token_secret = data['access_token_secret']
            self.watched_hashtags = data['watched_hashtags'] or []
        except KeyError:
            raise BadConfiguration
        try:
            self.friends_limit = int(data['friends_limit']) or 0
        except KeyError:
            self.friends_limit = 0
        try:
            self.favourites_limit = int(data['favourites_limit']) or 0
        except KeyError:
            self.favourites_limit = 0
        try:
            self.followers_limit = int(data['followers_limit']) or 0
        except KeyError:
            self.followers_limit = 0
        try:
            self.statuses_limit = int(data['statuses_limit']) or 0
        except KeyError:
            self.statuses_limit = 0
        try:
            self.retweeted_limit = int(data['retweeted_limit']) or 0
        except KeyError:
            self.retweeted_limit = 0
        try:
            self.follow_users = bool(data['follow_users']) or False
        except KeyError:
            self.follow_users = False
        try:
            self.blocked_users = data['blocked_users'] or []
        except KeyError:
            self.blocked_users = []
        try:
            self.blocked_hashtags = data['blocked_hashtags'] or []
        except KeyError:
            self.blocked_hashtags = []
        try:
            self.blocked_user_mentions = data['blocked_user_mentions'] or []
        except KeyError:
            self.blocked_user_mentions = []
        try:
            self.trigger_phrases = data['trigger_phrases'] or []
        except KeyError:
            self.trigger_phrases = []
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


    def set_logging(self, config):
        if config.lower() == 'debug':
            self.log_level = logging.DEBUG
        elif config.lower() == 'info':
            self.log_level = logging.INFO
        elif config.lower() == 'warn':
            self.log_level == logging.WARN
        elif config.lower() == 'error':
            self.log_level == logging.ERROR
        else:
            self.log_level == DEFAULT_LOG_LEVEL


    def tweet(self, tweet):
        if isinstance(tweet, str):
            try:
                self.api.update_status(tweet)
            except tweepy.TweepError as e:
                logging.info(e.reason)
        else:
            raise InvalidParameter


    def retweet(self, search):
        done = False
        while not done:
            for tweet in tweepy.Cursor(self.api.search, q=search).items():
                logging.info("Tweet by: @" + tweet.user.screen_name)
                self.is_worth_while_tweet(tweet) # to get data
                logging.info(tweet.text)
                answer = raw_input("[*] Retweet this tweet? [Y/n]: ")
                if not answer or answer == "Y" or answer == "y":
                    try:
                        tweet.favorite()
                        logging.info("Favorited the tweet")
                        if self.follow_users:
                            if not tweet.user.following:
                                tweet.user.follow()
                                logging.info("Followed the user")
                        tweet.retweet()
                        logging.info('Retweeted the tweet')
                        done = True
                        break
                    except tweepy.TweepError as e:
                        logging.info(e.reason)
                        continue
                else:
                    continue


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
                            self.api.update_status(tweet)
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


    def async_retweet(self):
        while True:
            if not self.running:
                break
            try:
                if self.is_operating_time():
                    tag = choice(self.watched_hashtags)
                    for tweet in tweepy.Cursor(self.api.search, q=tag).items():
                        # need moar white space!
                        for i in range(0,5):
                            logging.debug('----------------------------------')
                        logging.info('\nTweet by: @' + tweet.user.screen_name)
                        logging.info(tweet.text)
                        if self.is_worth_while_tweet(tweet):
                            try:
                                tweet.favorite()
                                logging.info('Favorited the tweet')
                            except tweepy.TweepError as e:
                                sleep(3)
                                logging.info(e.reason)
                                sleep(3)
                            if self.follow_users:
                                if not tweet.user.following:
                                    try:
                                        tweet.user.follow()
                                        logging.info('Followed the user')
                                        sleep(3)
                                    except tweepy.TweepError as e:
                                        logging.info(e.reason)
                                        sleep(3)
                            try:
                                tweet.retweet()
                                logging.info('Retweeted the tweet')
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
        logging.info("Retweeted: %s" % tweet.retweeted)
        logging.info("Friends: %s" % str(tweet.author.friends_count))
        logging.info("Favourites: %s" % str(tweet.author.favourites_count))
        logging.info("Followers: %s" % str(tweet.author.followers_count))
        logging.info("Statuses : %s" % str(tweet.author.statuses_count))
        logging.info("Reweets: %s" % str(tweet.retweet_count))
        for blocked in self.blocked_users:
            if not isinstance(blocked, str):
                continue
            if blocked.lower().replace('@', '') == \
                    tweet.user.screen_name.lower().replace('@', ''):
                return self.log_filtered('blocked_user_filter')
        if self.friends_limit:
            if int(tweet.user.friends_count) < int(self.friends_limit):
                return self.log_filtered('friends_limit')
        if self.favourites_limit:
            if int(tweet.author.favourites_count) < int(self.favourites_limit):
                return self.log_filtered('favourites_limit')
        if self.followers_limit:
            if int(tweet.author.followers_count) < int(self.followers_limit):
                return self.log_filtered('followers_limit')
        if self.statuses_limit:
            if int(tweet.author.statuses_count) < int(self.statuses_limit):
                return self.log_filtered('statuses_limit')
        if self.retweeted_limit:
            if int(tweet.retweet_count) < int(self.retweeted_limit):
                return self.log_filtered('retweet_limit')
        for blocked in self.blocked_hashtags:
            if not isinstance(blocked, str):
                continue
            for item in tweet.entities['hashtags']:
                if item['text'].lower() == blocked.replace('#', '').lower():
                    return self.log_filtered('hashtag_filter')
        for blocked in self.blocked_user_mentions:
            if not isinstance(blocked, str):
                continue
            for item in tweet.entities['user_mentions']:
                if item['screen_name'] == blocked.replace('@', ''):
                    return self.log_filtered('user_mention_filter')
        for blocked in self.trigger_phrases:
            if not isinstance(blocked, str):
                continue
            if blocked.lower() in tweet.text.lower():
                return self.log_filtered('trigger_phrase_filter')
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


    def auth(self):
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        return tweepy.API(auth)


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
