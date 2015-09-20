#
# Generate mutated files residing in the
# "samples" directory
#

import random
import os
import itertools  # cycle :)

import fileops
from helpers.queue import mutationQueue, processedQueue
from helpers.utils import random_alphabetical_string
from helpers.plugin_loader import get_plugins, load_plugin


class myFileGenerator():
    """
    Read input files from the samples directory
    and applies some modifications to them.
    It exposes the write_test_case(path) method
    """
    def __init__(self, debug = False):
        self.mutated_file_name = ""
        self.debug = debug
        parent = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        self.samples_dir = os.path.join(parent, 'samples')
        self.mutations_dir = os.path.join(parent, 'mutations')
        self.cthulhu = Cthulhu(self.debug)

        # Initialization. We will work on the mutations directory
        fileops.copy_all_files(self.samples_dir, self.mutations_dir)

    def _get_input_filename(self):
        """
        Gets a filename from the Mutation Queue
        Moves the Queue elements around
        (from mutation to processed one)
        """
        if mutationQueue.empty():
            # Mutation Queue is empty. Restore the elements
            # (from the processed Queue)
            while not processedQueue.empty():
                mutationQueue.put(processedQueue.get())

        e = mutationQueue.get()
        processedQueue.put(e)

        return e.filename

    def _gen_mutation(self):
        """
        Generates mutated contents from a sample file
        """
        input_file = self._get_input_filename()

        # Get the file extension
        extension = input_file.split('.')[-1]
        new_name = random_alphabetical_string(maxlen = 16, exact = True)
        self.mutated_file_name = "%s.%s" % (new_name, extension)

        input_filename = os.path.join(self.mutations_dir, input_file)

        with open(input_filename, 'rb') as f:
            original_contents = f.read()

        # Invoke Cthulhu! Yield a mutation!
        # Create an abomination!
        m = self.cthulhu.yield_mutation(original_contents)

        return m

    def write_test_case(self):
        """
        It creates the test case contents
        :return: Tuple (original, mutated) filenames or None
        """
        mutated_contents = self._gen_mutation()
        mutation_filename = os.path.join(self.mutations_dir, self.mutated_file_name)

        try:
            with open(mutation_filename, 'wb') as fh:
                fh.write(mutated_contents)

            return mutation_filename

        except:
            return None

    def delete_current_test_case(self):
        """
        Not interesting mutation.
        Kill it with fire.
        """
        mutation_filename = os.path.join(self.mutations_dir, self.mutated_file_name)
        os.remove(mutation_filename)


################################################################
# CTHULHU
################################################################
class Cthulhu(object):
    """
    This object encompases all mutations
    It is literally THE BRINGER OF DEATH
    Disclaimer: several parts have been shamelessly
    copied from Sulley Fuzzing Framework
    """
    def __init__(self, debug = False, mode = 'sequential'):
        self.mode = mode
        self.debug = debug
        self.plugin_list = []
        self.data_to_post = None
        print ""
        print "=== Initializing Cthulhu... ==="
        print "=== THE BRINGER OF DEATH... ==="
        print ""
        print "=== Initializing plugins... ==="
        self.initialize_plugins()

        self.cy_strings = itertools.cycle(self.get_common_strings())
        self.buffer_mutations = [
            #self.substitute_string,
            self.mutate_token,
            self.delete_block,
            self.swap_blocks,
            self.lift_bytes
            ]

    def initialize_plugins(self):
        """
        Load the selected plugins and makes
        them available to Cthulhu
        :return:
        """
        for p in get_plugins():
            print "=== Loading plugin %s..." % p['name']
            self.plugin_list.append(p)

    def apply_pre_processing(self, file_contents):
        """
        Applies the selected plugins in order to
        extract the raw data to be mutated
        :param file_contents: eeeh... the input file contents :)
        :return: extracted data
        """
        data = file_contents

        for p in self.plugin_list:
            plugin = load_plugin(p)
            data, self.data_to_post = plugin.pre(data)

        return data

    def apply_post_processing(self, mutated_buffer):
        """
        Applies the selected plugins in *reverse* order
        to recreate the original file format
        :param mutated_buffer: eeeh... the mutated buffer :)
        :return: new file contents
        """
        data = mutated_buffer

        for p in self.plugin_list[::-1]:
            # The plugins are applied in reverse order
            plugin = load_plugin(p)
            data = plugin.post(data, self.data_to_post)

        return data

    def yield_mutation(self, file_contents = None):
        """
        This is the meat and potatoes!!!1!
        Generators are cool
        Itertools are better!
        """
        if file_contents:
            # Mutations processing our file input are called randomly
            # This is something analogous to an
            # array of function pointers in C/C++
            f_idx = random.randrange(len(self.buffer_mutations))
            fp = self.buffer_mutations[f_idx]

            #
            # Pre-processing of buffer (plugin)
            #
            buf = self.apply_pre_processing(file_contents)

            mutated_buffer = fp.__call__(buf)

            #
            # Post-processing of mutated buffer (plugin)
            #
            new_file_contents = self.apply_post_processing(mutated_buffer)

            return new_file_contents

        else:
            # Crappy fallback
            # to predefined byte arrays
            return "A" * 1024

    def lift_bytes(self, buf):
        """
        Increases byte values from a
        random segment by a random value
        """
        offset = random.randrange(len(buf))
        tlen = random.randint(1, len(buf) - offset)
        token = buf[offset : offset + tlen]

        delta = random.randint(1, 255)
        replacement = ''.join([chr((ord(x) + delta) % 255) for x in token])
        mod_buf = buf[ : offset] + replacement + buf[offset + tlen : ]

        if self.debug:
            print "=== [debug] lift bytes"
            print mod_buf

        return mod_buf

    def substitute_string(self, buf):
        """
        Simple substitution with *standard tokens*
        This is equivalent to smash the original bytes
        """
        replacement = self.cy_strings.next()
        rlen = len(replacement)
        offset = random.randrange(len(buf))

        mod_buf = buf[ : offset] + replacement
        # Only in case the replacement fits into
        # the original buffer
        if offset + rlen < len(buf):
            mod_buf += buf[offset + rlen : ]

        if self.debug:
            print "=== [debug] Substitute string"
            print mod_buf

        return mod_buf

    def mutate_token(self, buf):
        """
        Mutates a token (subset from the buffer)
        and substitutes it with its mutation
        """
        # Get the random token
        offset = random.randrange(len(buf))
        tlen = random.randint(1, len(buf) - offset)
        token = buf[offset : offset + tlen]
        mutated_token = self.get_token_mutation(token)

        mod_buf = buf[ : offset] + mutated_token
        # Only in case the replacement fits into
        # the original buffer
        if offset + tlen < len(buf):
            mod_buf += buf[offset + tlen : ]

        if self.debug:
            print "=== [debug] Mutate token"
            print mod_buf

        return mod_buf

    def delete_block(self, buf):
        """
        Exactly what it says :)
        Randomly selects a block and deletes it
        """
        offset = random.randrange(len(buf))
        dlen = random.randrange(1, len(buf) - offset + 1)

        mod_buf = buf[ : offset] + buf[offset + dlen : ]

        if self.debug:
            print "=== [debug] Delete block"
            print mod_buf

        return mod_buf

    def swap_blocks(self, buf):
        """
        Just swapping stuff
        """
        L = len(buf)

        if L < 2:
            # Impossible to swap
            return buf

        off1 = random.randrange(L/2)
        len1 = random.randint(1, (L/2) - off1)

        off2 = random.randrange(L/2, L)
        len2 = random.randint(1, L - off2)

        A = buf[ : off1]
        B = buf[off1 : off1 + len1]
        C = buf[off1 + len1 : off2]
        D = buf[off2 : off2 + len2]
        E = buf[off2 + len2 : ]

        if self.debug:
            print "=== [debug] Swap blocks"
            print A + D + C + B + E

        return A + D + C + B + E

    def get_token_mutation(self, t):
        """
        This is particularly effective for delimiters
        but it would be useful for other tokens
        :return: random element of list of tokens
        """
        token_mutations = []

        token_mutations.append(t * 2)
        token_mutations.append(t * 5)
        token_mutations.append(t * 10)
        token_mutations.append(t * 25)
        #token_mutations.append(t * 100)
        #token_mutations.append(t * 500)
        #token_mutations.append(t * 1000)

        # try ommitting the delimiter.
        token_mutations.append("")

        # if the delimiter is a space, try throwing out some tabs.
        if t == " ":
            token_mutations.append("\t")
            token_mutations.append("\t" * 2)
            token_mutations.append("\t" * 100)

        # toss in some other common delimiters:
        token_mutations.append(" ")
        token_mutations.append("\t")
        token_mutations.append("\t " * 100)
        token_mutations.append("\t\r\n" * 100)
        token_mutations.append("!")
        token_mutations.append("@")
        token_mutations.append("#")
        token_mutations.append("$")
        token_mutations.append("%")
        token_mutations.append("^")
        token_mutations.append("&")
        token_mutations.append("*")
        token_mutations.append("(")
        token_mutations.append(")")
        token_mutations.append("-")
        token_mutations.append("_")
        token_mutations.append("+")
        token_mutations.append("=")
        token_mutations.append(":")
        token_mutations.append(": " * 100)
        token_mutations.append(":7" * 100)
        token_mutations.append(";")
        token_mutations.append("'")
        token_mutations.append("\"")
        token_mutations.append("/")
        token_mutations.append("\\")
        token_mutations.append("?")
        token_mutations.append("<")
        token_mutations.append(">")
        token_mutations.append(".")
        token_mutations.append(",")
        token_mutations.append("\r")
        token_mutations.append("\n")
        token_mutations.append("\r\n" * 64)
        token_mutations.append("\r\n" * 128)
        token_mutations.append("\r\n" * 512)

        return token_mutations[random.randrange(len(token_mutations))]

    def get_common_strings(self, long_strings = False):
        """
        Produce generic (independent from input) strings.
        These are known to exercise some corner cases.
        """
        common_strings = [
        # omission.
        "",

        # strings ripped from spike (and some others I added)
        "/.:/"  + "A" * 5000 + "\x00\x00",
        "/.../" + "A" * 5000 + "\x00\x00",
        "/.../.../.../.../.../.../.../.../.../.../",
        "/../../../../../../../../../../../../etc/passwd",
        "/../../../../../../../../../../../../boot.ini",
        "..:..:..:..:..:..:..:..:..:..:..:..:..:",
        "\\\\*",
        "\\\\?\\",
        "/\\" * 5000,
        "/." * 5000,
        "!@#$%%^#$%#$@#$%$$@#$%^^**(()",
        "%01%02%03%04%0a%0d%0aASDF",
        "%01%02%03@%04%0a%0d%0aASDF",
        "/%00/",
        "%00/",
        "%00",
        "%u0000",
        "%\xfe\xf0%\x00\xff",
        "%\xfe\xf0%\x01\xff" * 20,

        # format strings.
        "%n"     * 100,
        "%n"     * 500,
        "\"%n\"" * 500,
        "%s"     * 100,
        "%s"     * 500,
        "\"%s\"" * 500,

        # some binary strings.
        "\xde\xad\xbe\xef",
        "\xde\xad\xbe\xef" * 10,
        "\xde\xad\xbe\xef" * 100,
        "\xde\xad\xbe\xef" * 1000,
        "\xde\xad\xbe\xef" * 10000,
        "\x00"             * 1000,

        # miscellaneous.
        "\r\n" * 100,
        "<>" * 500         # sendmail crackaddr (http://lsd-pl.net/other/sendmail.txt)
        ]

        if long_strings:
            # add some long strings.
            common_strings += self.gen_long_strings("A")
            common_strings += self.gen_long_strings("B")
            common_strings += self.gen_long_strings("1")
            common_strings += self.gen_long_strings("2")
            common_strings += self.gen_long_strings("3")
            common_strings += self.gen_long_strings("<")
            common_strings += self.gen_long_strings(">")
            common_strings += self.gen_long_strings("'")
            common_strings += self.gen_long_strings("\"")
            common_strings += self.gen_long_strings("/")
            common_strings += self.gen_long_strings("\\")
            common_strings += self.gen_long_strings("?")
            common_strings += self.gen_long_strings("=")
            common_strings += self.gen_long_strings("a=")
            common_strings += self.gen_long_strings("&")
            common_strings += self.gen_long_strings(".")
            common_strings += self.gen_long_strings(",")
            common_strings += self.gen_long_strings("(")
            common_strings += self.gen_long_strings(")")
            common_strings += self.gen_long_strings("]")
            common_strings += self.gen_long_strings("[")
            common_strings += self.gen_long_strings("%")
            common_strings += self.gen_long_strings("*")
            common_strings += self.gen_long_strings("-")
            common_strings += self.gen_long_strings("+")
            common_strings += self.gen_long_strings("{")
            common_strings += self.gen_long_strings("}")
            common_strings += self.gen_long_strings("\x14")
            common_strings += self.gen_long_strings("\xFE")   # expands to 4 characters under utf16
            common_strings += self.gen_long_strings("\xFF")   # expands to 4 characters under utf16

        return common_strings

    def gen_long_strings(self, sequence, max_len = 0):
        """
        Given a sequence, generate a number of selectively chosen
        strings lengths of the given sequence.
        NOTE: argument max_len sets a... you got it, maximum length
        """

        long_strings = []
        for length in [128, 255, 256, 257, 511, 512, 513, 1023, 1024, 2048, 2049, 4095, 4096, 4097, 5000, 10000, 20000, 32762, 32763, 32764, 32765, 32766, 32767, 32768, 32769, 0xFFFF-2, 0xFFFF-1, 0xFFFF, 0xFFFF+1, 0xFFFF + 2, 99999, 100000, 500000, 1000000]:

            if max_len and length > max_len:
                break

            long_string = sequence * length
            long_strings.append(long_string)

        return long_strings
