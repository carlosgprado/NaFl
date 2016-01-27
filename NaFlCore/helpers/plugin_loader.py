#
# Plugin Loader
# Keep it simple, stupid:
# https://lkubuntu.wordpress.com/2012/10/02/writing-a-python-plugin-api/
#

import imp
import os

from config import nConfig

PluginFolder = './plugins'
MainModule = '__init__'

myConfig = nConfig()


def get_plugins():
    plugins = []
    possible_plugins = os.listdir(PluginFolder)

    for p in possible_plugins:
        # Plugins must be explicitly selected
        # in the config.ini file
        try:
            pc = myConfig.cfg.getboolean('plugins', p)
            if pc:
                print "Found configured plugin: %s" % p
            else:
                continue

        except KeyError:
            # Option not defined in config file
            continue

        location = os.path.join(PluginFolder, p)
        if not os.path.isdir(location) or not MainModule + '.py' in os.listdir(location):
            continue
        info = imp.find_module(MainModule, [location])
        plugins.append({'name': p, 'info': info})

    return plugins


def load_plugin(plugin):
    return imp.load_module(MainModule, *plugin['info'])

