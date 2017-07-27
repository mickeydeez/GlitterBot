#!/usr/bin/env python3

from lib.client import Client
from threading import Thread

import pprint
import logging


class Crawler(object):
    
    def __init__(self, config_path, seed):
        self.seed = seed
        self.client = Client(config_path, log=True)
        self.client.dump_stats(user=self.seed)
        self.client.extended_stats(user=self.seed)
        self.pp = pprint.PrettyPrinter(depth=6)

    def start_crawler(self):
        pass
