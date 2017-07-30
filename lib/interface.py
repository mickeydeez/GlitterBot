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
        self.rpad_value = 10
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
                self.reset_index()
                self.daemon.log_handler.emit(
                    "Rate Limit Error: %s" % datetime.now().strftime('%c'),
                    rec_type='error'
                )
                sleep(1)
            except KeyboardInterrupt:
                print("[*] Stopping threads. This may take a while depending on sleep times.")
                print("[*] You may need to hit Ctrl-C a couple more times :p")
                self.stop_threads()
                self.daemon.stop_threads()
                sys.exit()
            except curses.error:
                self.reset_index()
                print("[*] Window too short for entire display")
                sleep(1)
            except Exception as e:
                self.reset_index()
                self.daemon.log_handler.emit(e, rec_type='error')
                sleep(1)

    def stop_threads(self):
        self.running = False

    def user_interface(self, window):
        while True:
            if self.running:
                max_y, max_x = window.getmaxyx()
                window.resize(max_y, max_x)
                self.term_y_max = max_y - 1
                self.term_x_max = max_x - 1
                self.center = self.term_x_max / 2
                self.format_strings()
                self.clear_screen(window)
                self.dump_header(window)
                self.dump_account_info(window)
                self.dump_current_status(window)
                self.dump_recent_events(window)
                self.dump_errors(window)
                window.refresh()
                self.reset_index()
                sleep(1)
    
    def dump_header(self, window):
        self.dump_line(window, '')
        self.dump_line(window, self.header, inc=2, tab='center')
        self.dump_line(window, self.author_info, inc=2)
        self.dump_line(window, self.disclaimer)
        self.dump_line(window, '')

    def dump_account_info(self, window):
        self.dump_line(window, self.account_str)
        self.dump_line(window, self.uptime_str)
        self.dump_line(window, self.tweet_str)
        self.dump_line(window, self.retweet_str, inc=0)
        self.dump_line(window, self.config_reload_string, inc=1, tab='right')
        self.dump_line(window, self.follow_str, inc=0)
        self.dump_line(window, self.following_str, inc=1, tab='right')
        self.dump_line(window, self.fave_str, inc=0)
        self.dump_line(window, self.exit_help, inc=1, tab='right')
        self.dump_line(window, '')

    def dump_current_status(self, window):
        status_header = "[*] Current Status"
        self.dump_line(window, status_header)
        status_strings = self.format_status(self.current_status)
        self.dump_line(window, '')
        for string in status_strings:
            self.dump_line(window, string)
        self.dump_line(window, '')


    def dump_recent_events(self, window):
        self.dump_line(window, "[*] Recent Events")
        for item in self.daemon.log_handler.recent_logs:
            item.encode('utf-8')
            try:
                lim = self.term_x_max - (self.ltab_value + self.rpad_value)
                if len(item) > lim:
                    data = '  - %s%s' % (
                        item.replace('\n', '(nl)')[:lim],
                        '...' if len(item) > lim else ''
                    )
                    self.dump_line(window, data)
                else:
                    data = '  - %s' % item
                    self.dump_line(window, data)
            except UnicodeEncodeError as e:
                error = "  - Print Error: %s" % e
                self.dump_line(window, error)
        self.dump_line(window, '')

    def dump_errors(self, window):
        if len(self.daemon.log_handler.recent_errors) > 0:
            error_header = "[*] Errors"
            self.dump_line(window, error_header)
            for item in self.daemon.log_handler.recent_errors:
                data = " - %s" % item
                self.dump_line(window, data)
        else:
            no_error = "[*] There have been no unexpected problems"
            self.dump_line(window, no_error)
        self.dump_line(window, '')
    
    def format_status(self, status):
        status_strings = []
        if len(status) > (self.term_x_max - (self.ltab_value + self.rpad_value)):
            lim = self.term_x_max - (self.ltab_value + self.rpad_value)
            words = status.split()
            index = 0
            while True:
                string = ''
                for item in words[index:]:
                    if (len(string) + len(item)) < lim:
                        string = "%s%s " % (string, item)
                        index += 1
                    else:
                        break
                if index >= len(words):
                    if string != '':
                        status_strings.append(string)
                    break
                else:
                    status_strings.append(string)
        else:
            status_strings.append(status)
        return status_strings
    
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
        self.max_rtab = self.term_x_max
        window.erase()

    def determine_center_pos(self, length):
        return self.center - (length / 2)

    def determine_ltab_pos(self, length):
        return self.ltab_value

    def determine_rtab_pos(self, length):
        val = (self.term_x_max - self.rpad_value - length)
        if val < self.max_rtab:
            self.max_rtab = val
        return self.max_rtab

    def reset_index(self):
        self.index = 0

    def dump_line(self, window, data, inc=1, tab='left'):
        if tab == 'left':
            window.addstr(
                self.index,
                self.determine_ltab_pos(len(data)),
                data
            )
        elif tab == 'right':
            window.addstr(
                self.index,
                self.determine_rtab_pos(len(data)),
                data
            )
        elif tab == 'center':
            window.addstr(
                self.index,
                self.determine_center_pos(len(data)),
                data
            )
        self.index += inc

