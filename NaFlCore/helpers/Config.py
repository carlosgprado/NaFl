#
# Central repository for the config data
# I'm guessing this is very tacky CS but I
# don't know any better. In case you do,
# I'll be happy to hear :)
#

import os
from ConfigParser import SafeConfigParser


class nConfig():
    def __init__(self):
        """

        :return:
        """
        self.cfg = SafeConfigParser()
        self.cfg.read('config.ini')
