#
# The core (Python) reads the feedback information from
# the PinTool (C++) from the shared memory
#

import sys
import mmap
import subprocess
from array import array
import logging
import logging.handlers

try:
    import cPickle as pickle

except:
    import pickle

from helpers import utils
from helpers import fileops
from helpers.config import nConfig
from helpers.mutator import myFileGenerator
from helpers.queue import mutationQueue, FileToMutate
from helpers.crash_analysis import analyze_crash


# Modified in config file
DEBUG = False

# Shared memory
shm = None
shm_size = 0
history_bitmap = None

myConfig = nConfig()
cmd_l = []
ml = None  # main logger


def initialize_logging():
    """
    Printing to console is dirty
    """
    main_logger = logging.getLogger('main')

    LOG_FILENAME = 'logs\\log.txt'
    main_logger.setLevel(logging.DEBUG)

    # 5 rotating logs of 1 MB each
    handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME,
        maxBytes = 1024 * 1024,
        backupCount = 1
    )

    main_logger.addHandler(handler)

    return main_logger


def parse_config_file():
    """
    Initializes fuzzing parameters with
    information stored in a config file
    """
    global cmd_l
    global DEBUG

    # TODO: later this will be a GUI
    cmd_l.append(myConfig.cfg.get('pin_info', 'pin_bat'))
    cmd_l.append('-t')
    cmd_l.append(myConfig.cfg.get('pin_info', 'pintool'))
    cmd_l.append('-timer')
    cmd_l.append(myConfig.cfg.get('pin_info', 'timeout'))
    cmd_l.append('-module')
    cmd_l.append(myConfig.cfg.get('target_info', 'module'))
    cmd_l.append('-debug')
    cmd_l.append('1')
    cmd_l.append('--')
    cmd_l.append(myConfig.cfg.get('target_info', 'filename'))

    print cmd_l

    DEBUG = myConfig.cfg.getboolean('runtime', 'debug')


def is_interesting_input(curr_bitmap):
    """
    Compare the bitmap corresponding to the current
    trace with the history of taken paths.
    NOTE: the return values are different than the one
    used by AFL. These values can be used as priorities
    in a PriorityQueue()
    """
    global history_bitmap

    if curr_bitmap[0] == 0x41414141 \
            and curr_bitmap[1] == 0x42424242:
        # Crash!
        # TODO: move this to a parallel communication channel :)
        # Restore these first bytes to more appropriate values
        curr_bitmap[0] = 0
        curr_bitmap[1] = 0
        return 3

    # Go through all bytes
    for idx in xrange(len(curr_bitmap)):
        curr = curr_bitmap[idx]
        hist = history_bitmap[idx]

        # Is this a completely new tuple?
        if not hist and curr:
            history_bitmap[idx] = curr
            return 1

        # Hit count change? Moved to another bin?
        if utils.hit_bin(curr) > utils.hit_bin(hist):
            history_bitmap[idx] = curr
            return 2

    return 0


def run_under_pin(mutation_filename):
    """
    Runs the given file under PIN and
    gets the bitmap representing execution
    :returns: this bitmap
    """
    cmd_l.append(mutation_filename)
    subprocess.call(cmd_l, shell = False)
    cmd_l.pop()  # remove the filename from cmd :)

    # The PinTool has written its feedback into
    # the shared memory. Time to read it.
    shm.seek(0)  # file-like interface

    # This coerces somehow the bitmap to an array of ulong's
    curr_bitmap = array('L', shm.read(shm_size))  # C ulong (4 bytes)

    return curr_bitmap


def fuzzing_loop():
    """
    Fuzzing Loop.
    This loops (maybe indefinitely) creating several
    fuzzing processes
    """
    m_id = 0

    # Instantiate without params to deactivate debugging
    filegen = myFileGenerator(debug = DEBUG)

    # Initialize the Queue with the sample files
    ml.info("[*] Initializing queue...")

    for s in fileops.get_all_filenames(filegen.mutations_dir):
        mutationQueue.put(FileToMutate(0, s, m_id, None))
        m_id += 1

    ml.info("[*] Queue initialized with %d files" % m_id)
    ml.info("[*] Starting fuzzing process...")

    while True:
        # subprocess.call() is blocking, exactly what I need :)
        # Execution continues when this subprocess returns, either:
        # * instrumented process exits
        # * instrumented process crashes
        # * timeout expires (implemented in PinTool)

        m_id += 1

        # This generates the mutations and
        # it writes the current test file
        mutation_filename = filegen.write_test_case()

        if mutation_filename:
            mutation_bitmap = run_under_pin(mutation_filename)

        else:
            continue

        # Get the bitmap of the original file (mutation parent)
        interesting = is_interesting_input(mutation_bitmap)

        if not interesting:
            # Uninteresting. Throwing away this mutation.
            filegen.delete_current_test_case()

        elif interesting == 1:
            # ml.info("*** id: %d: Interesting file. Caused a whole new path. ***" % m_id)
            mutationQueue.put(FileToMutate(1, mutation_filename, m_id, mutation_bitmap))

        elif interesting == 2:
            # ml.info("*** id: %d: The hit count moved to another bin. ***" % m_id)
            mutationQueue.put(FileToMutate(2, mutation_filename, m_id, mutation_bitmap))

        elif interesting == 3:
            ml.info('**** CRASH ****' * 4)
            ml.info(mutation_filename)

            cmd = [myConfig.cfg.get('target_info', 'filename'), mutation_filename]
            # Analyzes the crash (and saves it, if determined interesting)
            analyze_crash(cmd)


def main():
    """
    This creates a shared memory region
    NOT backed up by a file
    """
    global shm
    global shm_size
    global history_bitmap
    global ml

    # Initialization stuff
    ml = initialize_logging()
    parse_config_file()
    s_uint32 = utils.get_size_uint32()
    bitmap_size = 65536
    shm_size = bitmap_size * s_uint32  # architecture dependent :)
    shm_name = "Local\\NaFlSharedMemory"

    ml.info("[*] Restoring saved bitmap from pickle file...")
    history_bitmap = fileops.restore_saved_bitmap()

    if not history_bitmap:
        ml.info("[x] Failed to restore saved bitmap! Starting from scratch.")
        history_bitmap = array('L', [0] * bitmap_size)

    shm = mmap.mmap(0,
                    shm_size,
                    shm_name,
                    access = mmap.ACCESS_WRITE
                    )

    if not shm:
        # Oops!
        ml.info('[x] Could not create the shared memory region')
        ml.info('[x] Aborting...')
        return

    # Some logging :)
    ml.info("")
    ml.info("=" * 80)
    ml.info("Started fuzzing: %s" % myConfig.cfg.get('target_info', 'filename'))
    ml.info("=" * 80)

    try:
        fuzzing_loop()  # never returns

    except KeyboardInterrupt:
        print '===                                      ==='
        print '=== Fuzzing cancelled by user (Ctrl + C) ==='
        print '=== Exiting...                           ==='
        print '===                                      ==='

        # Save the bitmap to a pickle file
        ml.info("[*] Saving the bitmap to file...")

        with open('saved_bitmap.p', 'wb') as fp:
            pickle.dump(history_bitmap, fp)

        sys.exit(1)


if __name__ == '__main__':
    main()
