#
# File operations :)
#

import glob
import os
import shutil
import random

try:
    import cPickle as pickle

except:
    import pickle

import utils


def append_serial(filename, c):
    """
    Uniquely name the files
    test.123.txt
    """
    # TODO: Dots in the path will be an issue
    name, ext = filename.split('.')
    new_name = '.'.join([name, str(c)])

    return '.'.join([new_name, ext])


def copy_all_files(source_dir, dest_dir):
    """
    It does what it says :)
    """
    print "=== [*] Copying all files from %s to %s" % (source_dir, dest_dir)

    for filename in glob.glob(os.path.join(source_dir, '*.*')):
        shutil.copy(filename, dest_dir)


def save_crash_file(crash_file, crash_dir):
    """
    Convenience wrapper
    """
    print "=== [*] Saving crash file (locally): %s" % crash_file

    shutil.move(crash_file, crash_dir)


def get_random_filename(dir):
    """
    It returns a random filename from a directory
    """
    files = os.listdir(dir)
    if files:
        rand_idx = random.randint(0, len(files) - 1)
        return files[rand_idx]
    else:
        raise Exception('Directory is empty!')


def get_all_filenames(dir):
    """
    Returns a list of absolute filename + path
    within the given directory
    """
    return glob.glob(os.path.join(dir, '*.*'))


def cleanup_old_mutations(dir):
    """
    Existing mutation.xxx files from old runs
    could be a problem. Erase them before.
    """
    print '=== [*] Cleaning up mutations from older runs...'
    mut_files = glob.glob(os.path.join(dir, 'mutation.*'))

    for m in mut_files:
        os.remove(m)


def rename_file(old, new):
    """
    Just a convenience wrapper
    """
    os.rename(old, new)


def gen_random_filename(mutations_dir, orig_name):
    """
    FIXME: things like mutation, crash, etc. dirs
    should be read from a config file and be
    available globally
    """
    suffix = orig_name.split('.')[-1]
    random_string = utils.random_alphabetical_string(20, True)
    random_filename = random_string + '.' + suffix

    return os.path.join(mutations_dir, random_filename)


def restore_saved_bitmap():
    """
    Restore the saved bitmap from a
    pickle dump to a file (or returns None)
    """
    filename_p = 'saved_bitmap.p'

    print "=== [*] Restoring saved bitmap from %s..." % filename_p

    if os.path.isfile(filename_p):
        with open(filename_p, 'rb') as fp:
            return pickle.load(fp)

    else:
        return None


def get_base64_contents(file):
    """
    Exactly that
    :param file: filename + path
    :return: None or Base64 string
    """
    try:

        with open(file, 'rb') as f:
            return f.read().encode('base64')

    except:
        return None
