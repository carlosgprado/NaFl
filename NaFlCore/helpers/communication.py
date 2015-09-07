#
# Communications module (with the server)
# TODO: make this more general (a factory maybe?)
#

import time
import platform
import xmlrpclib
from ConfigParser import SafeConfigParser

# TODO: read this centrally?
# Configuration file stuff
cfg = SafeConfigParser()
cfg.read('config.ini')


class Communications():

    def __init__(self):

        # If we can not connect to the server,
        # at least keep working locally
        self._is_connected = True

        self._connect_to_server()

    def _connect_to_server(self):
        # TODO: get this from the config.ini file
        URL = cfg.get('server_info', 'url')
        PORT = cfg.get('server_info', 'port')
        URI = "%s:%s" % (URL, PORT)

        self.server = xmlrpclib.ServerProxy(URI)
        self.node_properties = self._get_platform_info()
        self.node_id = self.node_properties['node_name']

        node_information = (self.node_id, self.node_properties)

        # Registers the node on the server
        print '=== [*] Registering node on the server...'

        try:
            self.server.add_node(node_information)
            print 'X' * 60
            print 'X Node registered successfully :)'
            print 'X' * 60

        except:
            print '=== [!] Failed to register node on server!'
            print '=== [!] Working locally from now on...'
            self._is_connected = False

    def add_crash(self, crash_properties):
        """
        Convenience wrapper
        """

        # Check the communication to the server first!
        # TODO: Code for the case it is not reachable :)
        try:
            self.server.ping()

        except:
            self._is_connected = False

        #
        # Try to connect five times
        #
        rec = self._reconnect(5)

        if rec:
            self._is_connected = True
            crash_info = (self.node_id, crash_properties)
            ret = self.server.add_crash(crash_info)

            if ret:
                print '=== [*] Crash registered on server'

            else:
                print '=== [!] Failed to register crash on server!'

        else:
            print '=== [!] Unable to reconnect to server!'

    def _reconnect(self, times):
        """
        Try to connect back to the server
        """
        for x in xrange(times):

            print '=== [!] Disconnected. Trying to connect...'

            try:
                self.server.ping()
                print '==== [*] Reconnected :)'
                self._is_connected = True
                return True

            except:
                time.sleep(1)

        return False

    def _get_platform_info(self):
        """
        Information regarding the computer
        where the fuzzer is running
        """
        node_properties = {
            'node_name' : platform.node(),
            'os_release': platform.release(),
            'os_version': platform.version(),
            'machine'   : platform.machine(),
            'processor' : platform.processor()
        }

        return node_properties



communications = Communications()
