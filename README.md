# GlitterBot
Simple idea spreader :)


Usage: copy config.yml.sample to config.yml and edit fields to your needs

Run with `python glitterbot.py`



For the time being the threads are just constantly re-reading from the config/tweets everytime an action is performed. In the case of tweets, they are removed from the file after they are sent out to ensure they do not get retweeted. If they get put back in they will eventually be sent out again.  In the case of the config file, if you make a syntax mistake in the while the process is running it will likely crash the threads.
