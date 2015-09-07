#
# This is build around the magnificent winappdbg framework
# http://winappdbg.sourceforge.net/Debugging.html#the-crash-and-crashdao-classes
# Kudos to Mario Vilas!
#

from winappdbg import win32, Debug, Crash

try:
    from winappdbg import CrashDAO

except ImportError:
    raise ImportError("[!] Crash analysis: SQLAlchemy is not installed!")

import fileops
from communication import communications


# Globals...
file_info = None
victim_filename = None
crash_filename = None


def crash_event_handler(event):
    """
    This implements the whole logic.
    The code below triggered by an access violation
    is responsible for storing / doing whatever with the crash info
    """

    code = event.get_event_code()

    # TODO: use this to distinguish between Eip and Rip?
    bits = event.get_process().get_bits()

    # If the event is a crash...
    if code == win32.EXCEPTION_DEBUG_EVENT and event.is_last_chance():
        print "=== [*] Crash detected, analyzing..."

        name = event.get_exception_description()
        pc = event.get_thread().get_pc()

        # Get the offending address.
        address = event.get_exception_address()

        # TODO: Get the register values
        #thread = event.get_thread()
        #registers = thread.get_context()

        # Generate a minimal crash dump.
        crash = Crash(event)

        if crash.exceptionLabel:
            c_label = crash.exceptionLabel

        else:
            c_label = 'Not available'

        # Crashing file contents in Base64
        if file_info:
            bin = file_info

        else:
            bin = None

        crash_properties = dict()
        crash_properties['victim'] = victim_filename
        crash_properties['processor'] = crash.arch
        crash_properties['event_name'] = name
        crash_properties['ip'] = address     # pc, registers['Eip'], etc.
        crash_properties['crash_label'] = c_label
        crash_properties['stacktrace'] = crash.stackTraceLabels
        crash_properties['exploitability'] = crash.isExploitable()
        crash_properties['bin'] = bin

        # TODO: Calculate some kind of metric in order to discard already
        # found crashes (or minimal variations of them)
        # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

        # You can turn it into a full crash dump (recommended).
        # crash.fetch_extra_data( event, takeMemorySnapshot = 0 ) # no memory dump
        crash.fetch_extra_data( event, takeMemorySnapshot = 1 ) # small memory dump
        # crash.fetch_extra_data(event, takeMemorySnapshot = 2) # full memory dump

        # TODO: do not hardcode this directory
        dao = CrashDAO("sqlite:///crashes/crashes.sqlite")

        # Store the crash dump in the database.
        print "=== [*] Storing crash dump in (local) database..."
        # NOTE: If you do this instead, heuristics are used to detect duplicated
        # crashes so they aren't added to the database.
        # dao.add( crash, allow_duplicates = False )
        dao.add(crash)

        #
        # Store the crash, locally and in server
        #

        # Kill the process.
        event.get_process().kill()

        communications.add_crash(crash_properties)
        fileops.save_crash_file(crash_filename, 'crashes')


def analyze_crash(cmd):
    """
    This is called with the command line (including the filename)
    which caused the crash before.
    It is a late analysis routine which sorts the crashes.
    """

    global file_info
    global victim_filename
    global crash_filename

    # TODO: This may not always be the case
    victim_filename, crash_filename = cmd
    print "=== [*] Analyzing %s" % crash_filename
    file_binary = fileops.get_base64_contents(crash_filename)

    if file_binary:
        file_info = (crash_filename, file_binary)

    # Instance a Debug object, passing it the event handler callback.
    debug = Debug(crash_event_handler, bKillOnExit = True)
    try:

        # Start a new process for debugging.
        debug.execv(cmd)

        # Wait for the debugee to finish.
        debug.loop()

    # Stop the debugger.
    finally:
        debug.stop()
