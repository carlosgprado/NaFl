#
# Command Line Application to ease with 
# Crash database maintenance
#

import os
import sys
import sqlite3 as sqlite
import cmd


class CrashDBCmd(cmd.Cmd):
    """
    Simple command line processor example.
    Shelling out is implemented.
    """
    # These properties control the
    # graphical appearence
    last_output = ''
    ruler = '_'

    def banner(self):
        print '*' * 80
        print "Welcome to my shinny command line application"
        print '*' * 80
        print

    def do_prompt(self, line):
        """
        Change the interactive prompt
        """
        if line:
            self.prompt = "(%s) " %line
        else:
            print 'Please specify a prompt text'

    def do_shell(self, line):
        """
        Run a shell command
        """
        print 'Running shell command:', line
        output = os.popen(line).read()
        print output
        self.last_output = output

    def do_echo(self, line):
        """
        Print the input, replacing '$out' with the
        output of the last shell command
        """
        print line.replace('$out', self.last_output)

    def do_greet(self, person):
        """
        Greet the person
        """
        if person and person in self.FRIENDS:
            greeting = 'hi, %s' % person
        else:
            greeting = 'hello'

        print greeting

    def complete_greet(self, text, line, begidx, endidx):
        """
        This is used for custom autocompletions
        Ex: the arguments are read from a db, etc.
        """
        if not text:
            completions = self.FRIENDS[:]
        else:
            completions = [f for f in self.FRIENDS if f.startswith(text)]

        return completions

    def do_resetdb(self, line):
        """
        Clears the DB
        """
        self.db.empty_db()
        
    def preloop(self):
        """
        Executed once before the Cmd prompt
        """
        self.banner()
        self.db = CrashDBConnector('fuzz.db')

    def postloop(self):
        """
        Executed once after the Cmd prompt
        """
        print
        print 'Bye!'

    def do_quit(self, line):
        """
        Quits the application, obviously
        """
        return True


class CrashDBConnector():
    def __init__(self, sqlite_file):
        print 'Initializing DB connector...'
        self.con = None
        self.cur = None
        self.file = sqlite_file

        self.connect_to_db()

    def connect_to_db(self):
        """
        Open a connection to the SQLite DB
        """
        try:
            self.con = sqlite.connect(self.file)
            self.cur = self.con.cursor()
            print 'Connected to', self.file

        except sqlite.Error, e:
            if self.con:
                self.con.rollback()

            print 'Error connecting to', self.file
            print 'Exception follows:'
            print e
            print 'Quitting...'
            sys.exit(1)

    def empty_db(self):
        """
        Resets the database to its initial
        state (empty, in this case)
        """
        try:
            self.cur.execute("DELETE FROM Crashes;")
            print 'Deleted all records'

        except sqlite.Error, e:
            print 'Unable to delete all records.'
            print 'Exception follows:'
            print e


if __name__ == '__main__':
    CrashDBCmd().cmdloop()
