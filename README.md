**Glitterbot - A Simple Idea Spreader**

----------

**Introduction**

Glitterbot will read in it's configuration and begin to interact with twitter based off criteria therein.


**Usage**

 - `pip install -r requirements.txt # Install requirements`
 - Copy config.yml.sample to config.yml and edit fields to your needs
 - To see available arguments run `python glitterboy.py`
 - In daemon mode you can trigger a dump of your user stats by sending the process a SIGUSR1

*NOTE: Works well with screen. Have screen append to logfile and detach from the process*
