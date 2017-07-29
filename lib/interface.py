#!/usr/bin/env python3

from time import sleep
from tweepy.error import RateLimitError
from threading import Timer

import curses

class CursesInterface(object):

    def __init__(self, daemon):
        self.daemon = daemon
        self.running = True
        self.update_user_status()
        self.get_account_stats()
        self.index = 0
        self.art = "`'*'`"*3
        self.header = "%s GlitterBot %s" % ( self.art, self.art )

    def run(self):
        while True:
            try:
                curses.wrapper(self.user_interface)
            except RateLimitError:
                pass
            except KeyboardInterrupt:
                print("[*] Stopping threads. This may take a while depending on sleep times.")
                print("[*] You may need to hit Ctrl-C a couple more times :p")
                self.stop_threads()
                self.daemon.stop_threads()
                break
            except:
                print("[*] Curses error. Will attempt to fix myself.")
                print("[*] You may need to resize your terminal")
                sleep(1)
                pass

    def stop_threads(self):
        self.running = False

    def user_interface(self, window):
        while True:
            if self.running:
                self.format_strings()
                self.clear_screen(window)
                self.dump_header(window)
                self.dump_account_info(window)
                self.dump_current_status(window)
                self.dump_recent_events(window)
                self.dump_errors(window)
                window.refresh()
                self.index = 0
                sleep(1)

    def update_user_status(self):
        if self.running:
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

    def dump_current_status(self, window):
        self.index += 2
        window.addstr(self.index, 10, "[*] Current Status")
        self.index += 1
        window.addstr(self.index, 10, "\t- %s" % self.current_status)

    def dump_recent_events(self, window):
        self.index += 3
        window.addstr(self.index, 10, "[*] Recent Events")
        self.index += 1
        for item in self.daemon.log_handler.recent_logs:
            try:
                window.addstr(
                    self.index,
                    14,
                    '- %s%s' % (
                        item.replace('\n', '(nl)')[:90],
                        '...' if len(item) > 90 else ''
                    )
                )
            except UnicodeEncodeError as e:
                window.addstr(self.index, 14, "- Error: %s" % e)
            self.index += 1

    def dump_errors(self, window):
        self.index += 2
        if len(self.daemon.log_handler.recent_errors) > 0:
            window.addstr(self.index, 10, "[*] Recent Errors")
            self.index += 1
            for item in self.daemon.log_handler.recent_errors:
                window.addstr(
                    self.index,
                    14,
                    '- %s' % item
                )
                self.index += 1
        else:
            window.addstr(self.index, 10, '[*] There have been no uncaught exceptions!')

    def get_account_stats(self):
        if self.running:
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

    def clear_screen(self, window):
        for i in range(30):
            whitespace = ' ' * 150
            window.addstr(i, 10, whitespace)

    def dump_header(self, window):
        self.index += 1
        window.addstr(self.index, 10, self.header)
        self.index += 1
        window.addstr(self.index, 10, "Author: mickey")
        self.index += 1
        window.addstr(
            self.index,
            10,
            "REMEMBER: Always be careful clicking links. Best to verify from the account first."
        )

    def dump_account_info(self, window):
        self.index += 2
        window.addstr(self.index, 10, self.account_str)
        self.index += 1
        window.addstr(self.index, 10, self.uptime_str)
        self.index += 1
        window.addstr(self.index, 10, self.tweet_str)
        self.index += 1
        window.addstr(self.index, 10, self.retweet_str)
        window.addstr(self.index, 45, self.config_reload_string)
        self.index += 1
        window.addstr(self.index, 10, self.follow_str)
        window.addstr(self.index, 45, self.following_str)
        self.index += 1
        window.addstr(self.index, 10, self.fave_str)
        window.addstr(self.index, 45, "Press Ctrl-C to initiate a terminate sequence")

