#
# NaFl server side database operations
# SQLite is beautiful
#

import sqlite3 as sqlite
import sys


class CrashDataBase():
    """
    Some convenience wrappers for the
    SQLite database operations
    """
    def __init__(self):
        """
        Simplicity is better than complexity
        """
        try:
            self.con = sqlite.connect('fuzz.db')
            self.cur = self.con.cursor()

            self.cur.executescript("""
                CREATE TABLE IF NOT EXISTS Crashes ( \
                Id INTEGER PRIMARY KEY, \
                NodeId TEXT, \
                Victim TEXT, \
                Cpu TEXT, \
                EventName TEXT, \
                Ip TEXT, \
                StackTrace TEXT, \
                CrashLabel TEXT, \
                Exploitable TEXT, \
                FileName TEXT);
                """)

            self.con.commit()

            print '=== [*] Database initialized successfully :)'

        except sqlite.Error, e:
            if self.con:
                self.con.rollback()

            print "=== [!] Error %s:" % e.args[0]
            sys.exit(1)


    def write_crash(self, crash_properties):
        """
        Process data to a format suitable for
        storage in the SQLite database
        """
        node = crash_properties['node_id']
        victim_pathname = crash_properties['victim']
        cpu = crash_properties['processor']
        event_name = crash_properties['event_name']
        ip = crash_properties['ip']
        cl = crash_properties['crash_label']
        exp = crash_properties['exploitability'][0]
        filename = crash_properties['filename']

        victim_filename = victim_pathname.split('\\')[-1]
        # This is a tuple, stringify it or die trying
        try:
            stack_trace = ', '.join(crash_properties['stacktrace'])

        except:
            stack_trace = 'Not available'

        self.cur.execute("INSERT INTO Crashes(NodeId, Victim, Cpu, EventName, Ip, StackTrace, CrashLabel, Exploitable, FileName) \
                         VALUES('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" \
                         % (node, victim_filename, cpu, event_name, ip, stack_trace, cl, exp, filename))

        self.con.commit()


    def retrieve_crashes(self):
        """
        Gets all crash information
        :return: iterator of tuples
        """
        self.cur.execute("SELECT * FROM Crashes")
        rows = self.cur.fetchall()

        return rows


crash_database = CrashDataBase()
