#
# XMLRPC Server
# Fuzzer nodes connect to this in order to
# communicate their progress / findings
#
# It makes use of Python Twisted
# Not that it is necessary, it's just
# a HIPSTER thing :)
#

from twisted.web import xmlrpc
from twisted.web.server import Site
from twisted.internet import reactor

from database import crash_database
from collections import defaultdict
import os
import logging

# Set up logging
# TODO: convert this to rotating logfiles
logging.basicConfig(level = logging.DEBUG)


################################################################
class Hive(xmlrpc.XMLRPC):
    """ Hive object to be published. """

    def __init__(self):
        # These two are needed internally (by XMLRPC)
        self.allowNone = True
        self.useDateTime = False

        # dictionary with list elements
        # node_info[node_id] = [node_info1, node_info2, ...]
        self.node_info = defaultdict()

        # dictionary with list elements
        # crashes[node_id] = [crash_info1, crash_info2, ...]
        self.crashes = defaultdict()

        if not os.path.isdir('crashes'):
            os.mkdir('crashes')

    def xmlrpc_del_node(self, node_id):
        try:
            self.node_info.pop(node_id)
            return True

        except:
            return False


    def xmlrpc_add_node(self, node_info):
        (node_id, node_properties) = node_info
        self.node_info[node_id] = node_properties
        self.crashes[node_id] = list()
        logging.debug('Attached node: %s' % node_id)

        return True


    def xmlrpc_add_crash(self, crash_info):
        """
        Appends the crash info to the dictionary
        """
        (node_id, crash_properties) = crash_info
        crash_properties['node_id'] = node_id
        self.crashes[node_id].append(crash_properties)

        # Write to file
        if crash_properties['bin']:
            pathname, file_contents = crash_properties['bin']

            filename = pathname.split('\\')[-1]
            crash_properties['filename'] = filename

            crash_path_name = 'crashes' + os.sep + filename

            with open(crash_path_name, 'wb') as f:
                f.write(file_contents.decode('base64'))

        # Write to the local (server) SQLite
        crash_database.write_crash(crash_properties)
        logging.debug('Found crash from: %s' % node_id)

        return True


    def xmlrpc_ping(self):
        """
        Anybody there?
        """
        return 'pong!'


    #############################################################
    # The following methods will be queried by the web interface
    #############################################################
    def xmlrpc_get_node_info(self):
        """
        It returns the whole dictionary of node information
        """
        return self.node_info

    def xmlrpc_get_node_ids(self):
        """
        It returns a list of node ids
        """
        return self.node_info.keys()

    def xmlrpc_update_progress(self, node_id, count):
        """
        For now on "progress" means iteration count,
        in the future this could be code coverage or alike
        """
        pass

    def xmlrpc_fault(self):
        """
        TODO: Change this to something useful
        """
        raise xmlrpc.Fault(123, 'The fault procedure is faulty')


################################################################
if __name__ == '__main__':
    PORT = 7080
    h = Hive()
    reactor.listenTCP(PORT, Site(h))
    logging.debug('Starting the server in port %d', PORT)
    reactor.run()
