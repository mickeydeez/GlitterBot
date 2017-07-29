#!/usr/bin/env python3

from time import sleep
from tweepy.error import RateLimitError
from threading import Timer

import curses
import sys

class CursesInterface(object):

    def __init__(self, daemon):
        self.daemon = daemon
        self.running = True
        self.update_user_status()
        self.get_account_stats()
        self.index = 0
        self.ltab_value = 10
        self.rpad_value = 20
        self.art = "`'*'`"*3
        self.header = "%s GlitterBot %s" % ( self.art, self.art )
        self.author_info = "Author: Mickey"
        self.disclaimer = "REMEMBER: Always be careful clicking links. Best to verify from the account first."
        self.exit_help = "Press Ctrl-C to initiate a terminate sequence"
        reload(sys)
        sys.setdefaultencoding("utf-8")

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
                self.term_y_max = curses.LINES - 1
                self.term_x_max = curses.COLS - 1
                self.center = self.term_x_max / 2
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
    
    def dump_header(self, window):
        self.index += 1
        window.addstr(
            self.index,
            self.determine_center_pos(len(self.header)),
            self.header
        )
        self.index += 2
        window.addstr(
            self.index,
            self.determine_ltab_pos(len(self.author_info)),
            self.author_info
        )
        self.index += 1
        window.addstr(
            self.index,
            self.determine_ltab_pos(len(self.disclaimer)),
            self.disclaimer
        )

    def dump_account_info(self, window):
        self.index += 2
        window.addstr(
            self.index,
            self.determine_ltab_pos(len(self.account_str)),
            self.account_str
        )
        self.index += 1
        window.addstr(
            self.index,
            self.determine_ltab_pos(len(self.uptime_str)),
            self.uptime_str
        )
        self.index += 1
        window.addstr(
            self.index,
            self.determine_ltab_pos(len(self.tweet_str)),
            self.tweet_str
        )
        self.index += 1
        window.addstr(
            self.index,
            self.determine_ltab_pos(len(self.retweet_str)),
            self.retweet_str
        )
        window.addstr(
            self.index,
            self.determine_rtab_pos(len(self.config_reload_string)),
            self.config_reload_string
        )
        self.index += 1
        window.addstr(
            self.index,
            self.determine_ltab_pos(len(self.follow_str)),
            self.follow_str
        )
        window.addstr(
            self.index,
            self.determine_rtab_pos(len(self.following_str)),
            self.following_str
        )
        self.index += 1
        window.addstr(
            self.index,
            self.determine_ltab_pos(len(self.fave_str)),
            self.fave_str
        )
        window.addstr(
            self.index,
            self.determine_rtab_pos(len(self.exit_help)),
            self.exit_help
        )
    
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
        status_header = "[*] Current Status"
        window.addstr(
            self.index,
            self.determine_ltab_pos(len(status_header)),
            status_header
        )
        self.index += 1
        current_status = " - %s" % self.current_status
        if len(current_status) > (self.term_x_max - (self.ltab_value + self.rpad_value)):
            lim = self.term_x_max - (self.ltab_value + self.rpad_value)
            status_string = "%s..." % current_status[:lim]
        else:
            status_string = current_status
        window.addstr(
            self.index,
            self.determine_ltab_pos(len(status_string)),
            status_string
        )

    def dump_recent_events(self, window):
        self.index += 2
        window.addstr(self.index, 10, "[*] Recent Events")
        self.index += 1
        for item in self.daemon.log_handler.recent_logs:
            item.encode('utf-8')
            try:
                lim = self.term_x_max - (self.ltab_value + self.rpad_value)
                data = '  - %s%s' % (
                    item.replace('\n', '(nl)')[:lim],
                    '...' if len(item) > lim else ''
                )
                window.addstr(
                    self.index,
                    self.determine_ltab_pos(len(data)),
                    data
                )
                self.index += 1
            except UnicodeEncodeError as e:
                error = "  - Print Error: %s" % e
                window.addstr(
                    self.index,
                    self.determine_ltab_pos(len(error)),
                    error
                )
                self.index += 1

    def dump_errors(self, window):
        self.index += 2
        if len(self.daemon.log_handler.recent_errors) > 0:
            error_header = "[*] Errors"
            window.addstr(
                self.index,
                self.deteremine_ltab_pos(len(error_header)),
                error_header
            )
            self.index += 1
            for item in self.daemon.log_handler.recent_errors:
                data = " - %s" % item
                window.addstr(
                    self.index,
                    self.determine_ltab_pos(len(data)),
                    data
                )
                self.index += 1
        else:
            no_error = "[*] There have been no uncaught exceptions"
            window.addstr(
                self.index,
                self.determine_ltab_pos(len(no_error)),
                no_error
            )

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
        for i in range(self.term_y_max):
            whitespace = ' ' * self.term_x_max
            window.addstr(i, 0, whitespace)

    def determine_center_pos(self, length):
        return self.center - (length / 2)

    def determine_ltab_pos(self, length):
        return self.ltab_value

    def determine_rtab_pos(self, length):
        return self.center + (self.term_y_max - self.center)

