#!/usr/bin/env python3

from lib.client import Client
from threading import Thread

import pprint


class Crawler(object):
    
    def __init__(self, config_path, seed):
        self.seed = seed
        self.twit = Client(config_path, log=True)
        twit.dump_stats(user=self.seed)
        twit.extendded_stats(user=self.seed)
        self.pp = pprint.PrettyPrinter(depth=6)

    def start_crawler(self):
        pass
