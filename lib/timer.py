#!/usr/bin/env python3

import threading
import time

class Timer(threading.Thread):

    def __init__(self, timeout=3, sleep_chunk=0.25, callback=None, *args):
        threading.Thread.__init__(self)

        self.timeout = timeout
        self.sleep_chunk = sleep_chunk
        if callback == None:
            self.callback = None
        else:
            self.callback = callback
        self.callback_args = args

        self.terminate_event = threading.Event()
        self.start_event = threading.Event()
        self.reset_event = threading.Event()
        self.count = self.timeout/self.sleep_chunk

    def run(self):
        while not self.terminate_event.is_set():
            while self.count > 0 and self.start_event.is_set():
                if self.reset_event.wait(self.sleep_chunk):
                    self.reset_event.clear()
                    self.count = self.timeout/self.sleep_chunk
                self.count -= 1
            if self.count <= 0:
                self.start_event.clear()
                self.callback(*self.callback_args)
                self.count = self.timeout/self.sleep_chunk

    def start(self):
        self.start_event.set()

    def stop(self):
        self.start_event.clear()
        self.count = self.timeout / self.sleep_chunk

    def restart(self):
        if self.start_event.is_set():
            self.reset_event.set()
        else:
            self.start_event.set()

    def terminate(self):
        self.terminate_event.set()
