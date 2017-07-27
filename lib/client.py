#!/usr/bin/env python3

from lib.exceptions import BadConfiguration
from yaml import load
from six.moves.html_parser import HTMLParser

import tweepy
import logging


DEFAULT_LOG_LEVEL = logging.INFO


class Client(object):

    def __init__(self, config_path, log=True):
        self.config_path = config_path
        self.load_config()
        if log:
            logging.basicConfig(level=self.log_level,
                format='[%(levelname)s] (%(threadName)-10s) %(message)s'
            )
        self.api = self.auth()
        self.name = self.api.me().screen_name
        self.running = True


    def load_config(self):
        with open(self.config_path, 'r') as f:
            data = load(f.read())
        try:
            self.consumer_key = data['consumer_key']
            self.consumer_secret = data['consumer_secret']
            self.access_token = data['access_token']
            self.access_token_secret = data['access_token_secret']
            self.watched_hashtags = data['watched_hashtags'] or []
        except KeyError:
            raise BadConfiguration
        try:
            self.set_logging(data['log_level'])
        except KeyError:
            self.log_level = DEFAULT_LOG_LEVEL
            self.set_logging(DEFAULT_LOG_LEVEL)


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


    def dump_stats(self, user=None):
        if not user:
            data = self.api.me()
        else:
            if isinstance(user, str):
                data = self.api.get_user('%s' % str(user.replace('@', '')))
            else:
                raise InvalidParameter
        logging.info("[*] Username: @%s" % data.screen_name)
        logging.info("[*] Name: %s" % data.name)
        logging.info("[*] Favourites: %s" % str(data.favourites_count))
        logging.info("[*] Followers: %s" % str(data.followers_count))
        logging.info("[*] Following: %s" % str(data.friends_count))
        logging.info("[*] Listed: %s" % str(data.listed_count))


    def extended_stats(self, user=None):
        if not user:
            data = self.api.me()
        else:
            if isinstance(user, str):
                data = self.api.get_user('%s' % str(user.replace('@', '')))
            else:
                raise InvalidParameter
        logging.info("[*] Created: %s" % data.created_at)
        logging.info("[*] Description: %s" % data.description)
        logging.info("[*] Last update: %s" % data.status.created_at)
        hashtags = ' '.join(
            [ "#%s" % x['text'] for x in \
             data.status.entities['hashtags']]
        )
        mentions = ' '.join(
            [ "@%s" % x['screen_name'] for x in \
                data.status.entities['user_mentions']]
        )
        logging.info("[*] \tUser Mentions: %s" % mentions)
        logging.info("[*] \tHashtags: %s" % hashtags)
        html = HTMLParser()
        if "RT @" in data.status.text:
            logging.info(
                "[*] \tRetweet Text: %s" % html.unescape(
                    data.status.text.replace('\n', '\n\t\t    ')
                )
            )
        else:
            logging.info(
                "[*] \tTweet Text: %s" % html.unescape(
                    data.status.text.replace('\n', '\n\t\t    ')
                )
            )
        logging.info('[*] \tRetweet Count: %s' % str(data.status.retweet_count))


    def retweet_loop(self, query):
        done = False
        while not done:
            for tweet in self.search(query):
                logging.info("Tweet by: @" + tweet.user.screen_name)
                self.dump_tweet_stats(tweet) # to get data
                logging.info(tweet.text)
                answer = raw_input("[*] Retweet this tweet? [Y/n]: ")
                if not answer or answer == "Y" or answer == "y":
                    try:
                        self.favourite(tweet)
                        self.retweet(tweet)
                        done = True
                        break
                    except tweepy.TweepError as e:
                        logging.info(e.reason)
                        continue
                else:
                    continue


    def dump_tweet_stats(self, tweet):
        logging.info("Retweeted: %s" % tweet.retweeted)
        logging.info("Following: %s" % str(tweet.author.friends_count))
        logging.info("Favourites: %s" % str(tweet.author.favourites_count))
        logging.info("Followers: %s" % str(tweet.author.followers_count))
        logging.info("Statuses : %s" % str(tweet.author.statuses_count))
        logging.info("Reweets: %s" % str(tweet.retweet_count))


    def search(self, query):
        return tweepy.Cursor(self.api.search, q=query).items()


    def follow(self, user):
        if not user.following:
            user.follow()
            logging.info("Followed @%s" % user.screen_name)
    
    
    def tweet(self, tweet):
        if isinstance(tweet, str):
            try:
                self.api.update_status(tweet)
            except tweepy.TweepError as e:
                logging.info(e.reason)
        else:
            raise InvalidParameter


    def retweet(self, tweet):
        if not tweet.retweeted:
            tweet.retweet()
            logging.info("Retweeted the tweet")


    def favourite(self, tweet):
        tweet.favorite()
        logging.info("Favorited the tweet")


    def auth(self):
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        return tweepy.API(auth)
