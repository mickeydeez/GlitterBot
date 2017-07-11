import tweepy
import threading
import logging
import random
import yaml
import os
from datetime import datetime
from time import sleep


CONFIG_PATH = 'config.yml'
DEFAULT_LOG_LEVEL = logging.DEBUG


def run():
    tweet_thread = threading.Thread(name='tweeter', target=tweeter)
    retweet_thread = threading.Thread(name='retweeter', target=retweeter)
    tweet_thread.setDaemon(True)
    retweet_thread.setDaemon(True)
    tweet_thread.start()
    retweet_thread.start()
    while threading.active_count() > 0:
        sleep(0.1)


class BadConfiguration(Exception):
    pass


class Tweeter(object):

    def __init__(self):
        self.reload_config()
        logging.basicConfig(level=self.log_level,
            format='[%(levelname)s] (%(threadName)-10s) %(message)s'
        )
        self.api = self.auth()
    
    
    def reload_config(self):
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = yaml.load(f.read())
        except:
            raise BadConfiguration
        if not isinstance(data['watched_hashtags'], list):
            raise BadConfiguration   
        try:
            if os.path.isfile(data['tweets_path']):
                self.tweets_path = data['tweets_path']
            else:
                raise BadConfiguration
        except:
            raise BadConfiguration
        try:
            self.min_hour = data['minimum_hour']
            self.max_hour = data['maximum_hour']
        except:
            raise BadConfiguration
        try:
            self.set_logging(data['log_level'])
        except:
            self.log_level = DEFAULT_LOG_LEVEL
        self.consumer_key = data['consumer_key']
        self.consumer_secret = data['consumer_secret']
        self.access_token = data['access_token']
        self.access_token_secret = data['access_token_secret']
        self.friends_limit = data['friends_limit']
        self.favourites_limit = data['favourites_limit']
        self.followers_limit = data['followers_limit']
        self.statuses_limit = data['statuses_limit']
        self.retweeted_limit = data['retweeted_limit']
        self.watched_hashtags = data['watched_hashtags'] or []
        self.blocked_hashtags = data['blocked_hashtags'] or []
        self.blocked_user_mentions = data['blocked_user_mentions'] or []


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


    def tweet(self):
        while True:
            self.tweets = self.load_tweets()
            if self.is_operating_time():
                tweet = random.choice(self.tweets)
                try:
                    # need moar white space!
                    for i in range(0,5):
                        logging.debug('----------------------------------')
                    logging.info(tweet)
                    if tweet != '\n':
                        self.api.update_status(tweet)
                        self.update_tweets(tweet)
                        sleep(1200)
                    else:
                        pass
                except tweepy.TweepError as e:
                    logging.info(e.reason)
                    sleep(300)
            else:
                self.reload_config()
                sleep(60) # just to save cpu cycles


    def retweet(self):
        while True:
            if self.is_operating_time():
                tag = random.choice(self.watched_hashtags)
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
                            sleep(3)
                        except tweepy.TweepError as e:
                            logging.info(e.reason)
                            sleep(2)
                        if not tweet.user.following:
                            try:
                                tweet.user.follow()
                                logging.info('Followed the user')
                                sleep(3)
                            except tweepy.TweepError as e:
                                logging.info(e.reason)
                                sleep(2)
                        try:
                            tweet.retweet()
                            logging.info('Retweeted the tweet')
                            sleep(180)
                        except tweepy.TweepError as e:
                            logging.info(e.reason)
                            sleep(5)
                        self.reload_config()
                        sleep(5)
                        break
                    else:
                        self.reload_config()
                        sleep(1)
                        continue
            else:
                self.reload_config()
                sleep(60)


    def is_worth_while_tweet(self, tweet):
        logging.debug("Retweeted: %s" % tweet.retweeted)
        logging.debug("Friends: %s" % str(tweet.author.friends_count))
        logging.debug("Favourites: %s" % str(tweet.author.favourites_count))
        logging.debug("Followers: %s" % str(tweet.author.followers_count))
        logging.debug("Statuses : %s" % str(tweet.author.statuses_count))
        logging.debug("Reweets: %s" % str(tweet.retweet_count))
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



def tweeter():
    twit = Tweeter()
    twit.tweet()


def retweeter():
    twit = Tweeter()
    while True:
        try:
            twit.retweet()
        except StopIteration:
            logging.debug("Hit query end")
            sleep(30)
            continue


if __name__ == '__main__':
    run()
