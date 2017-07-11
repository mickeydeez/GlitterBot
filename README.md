**Glitterbot - A Simple Idea Spreader**

----------

**Introduction**

Glitterbot will read in it's configuration and begin to interact with twitter based off criteria therein.


**Usage**

 - `pip install pyyaml tweepy # the rest should be built in`
 - Copy config.yml.sample to config.yml and edit fields to your needs
 - Run with `python glitterbot.py`

*NOTE: Works well with screen. Have screen append to logfile and detach from the process*

For the time being the threads are just constantly re-reading from the config/tweets everytime an action is performed. In the case of tweets, they are removed from the file after they are sent out to ensure they do not get retweeted. If they get put back in they will eventually be sent out again. In the case of the config file, if you make a YAML syntax mistake while the process is running it will likely crash the threads.
