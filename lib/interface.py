#!/usr/bin/env python3

from time import sleep
from tweepy.error import RateLimitError
from threading import Timer

import curses

class CursesInterface(object):

    def __init__(self, daemon):
        self.daemon = daemon
        self.update_user_status()
        self.get_account_stats()
        self.header = "*** GlitterBot ***"

    def run(self):
        while True:
            try:
                curses.wrapper(self.user_interface)
            except RateLimitError:
                pass

    def update_user_status(self):
        try:
            self.current_status = self.daemon.client.api.me().status.text.encode('utf-8').replace(
                '\n',
                '(nl)'
            )
        except Exception as e:
            self.current_status = "Error: %s" % e
        status_thread = Timer(
            30,
            self.update_user_status
        ).start()

    def dump_recent_events(self, window, index):
        for item in self.daemon.log_handler.recent_logs:
            try:
                window.addstr(
                    index,
                    14,
                    '- %s%s' % (
                        item.replace('\n', '(nl)')[:90],
                        '...' if len(item) > 90 else ''
                    )
                )
            except UnicodeEncodeError as e:
                window.addstr(index, 10, "\t- Error: %s" % e)
            index += 1

    def get_account_stats(self):
        self.userdata = self.daemon.client.api.me()
        userdata_thread = Timer(
            60,
            self.get_account_stats
        ).start()

    def format_strings(self):
        self.account_str = "[*] Account: %s" % self.daemon.client.name
        self.uptime_str = "[*] Uptime: %s" % self.daemon.uptime
        self.tweet_str = "[*] Total Tweets: %s" % self.daemon.total_tweets
        self.config_reload_string = "Last configuration reload: %s" % (
            self.daemon.last_config_reload.strftime('%c')
        )
        self.retweet_str = "[*] Total Retweets: %s" % self.daemon.total_retweets
        self.follow_str = "[*] Total Follows: %s" % self.daemon.total_follows
        self.fave_str = "[*] Total Favourites: %s" % self.daemon.total_favourites
        self.following_str = "Total Followers: %s" % self.userdata.followers_count


    def user_interface(self, window):
        while True:
            self.format_strings()
            for i in range(25):
                whitespace = ' ' * 150
                window.addstr(i, 10, whitespace)
            window.addstr(1, 10, self.header)
            window.addstr(3, 10, self.account_str)
            window.addstr(4, 10, self.uptime_str)
            window.addstr(5, 10, self.tweet_str)
            window.addstr(6, 10, self.retweet_str)
            window.addstr(6, 45, self.config_reload_string)
            window.addstr(7, 10, self.follow_str)
            window.addstr(7, 45, self.following_str)
            window.addstr(8, 10, self.fave_str)
            window.addstr(10, 10, "[*] Current Status")
            window.addstr(11, 10, "\t- %s" % self.current_status)
            window.addstr(13, 10, "[*] Recent Events")
            self.dump_recent_events(window, 14)
            i = 14
            window.refresh()
            sleep(2)

