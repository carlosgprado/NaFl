#
# Unzip / Zip plugin.
#
# Use this if the file format consumed by your application is
# zipped (for example, DOCX or alike)
#
# NOTE: There is a reason why these formats are zipped.
# Usually they contain a whole directory structure. This plugin will
# extract the contents of a single file within it.
#
# At the very least two functions must be defined:
#
# - pre(buf)
#   Takes the raw file input and prepares it to be consumed by Cthulhu.
#
# - post(buf)
#   Takes the mutated data and prepares it to be written back to file
#

import io
import zipfile
import random

file_extension = '.xml'
zin = None
extracted_file_name = ''


def pre(raw_data):
    """
    This plugin extracts the contents of a random file
    within the original Zip file
    :param raw_data: file contents
    :return: unmodified data
    """
    global extracted_file_name, zin

    # A file-like object is needed by ZipFile
    file_like_object = io.BytesIO(raw_data)
    zin = zipfile.ZipFile(file_like_object, 'r')
    selected_filename = get_random_filename()

    # I will need this later to restore the file
    extracted_file_name = selected_filename
    data = zin.read(selected_filename)

    return data


def post(mutated_data):
    """
    This is rather tricky since it is not possible to
    delete or update a file within a Zip file in Python
    It is necessary to create a new ZipFile object
    Thanks StackOverflow ;)
    :param mutated_data: data mutated by Cthulhu
    :return: unmodified data
    """
    file_like_object = io.BytesIO()
    zout = zipfile.ZipFile(file_like_object, 'w')
    for item in zin.infolist():
        # Copy everything verbatim, except the mutated item
        if item.filename == extracted_file_name:
            buf = mutated_data

        else:
            buf = zin.read(item.filename)

        zout.writestr(item, buf)

    # Cleanup
    zin.close()
    zout.close()

    return file_like_object


def get_random_filename():
    """
    Gets a random filename from inside the ZipFile object,
    with the selected file extension
    :return: arbitrary filename of selected type (extension)
    """
    filename_list = [x.filename for x in zin.filelist if x.filename.endswith(file_extension)]
    rand_idx = random.randint(0, len(filename_list) - 1)

    return filename_list[rand_idx]
