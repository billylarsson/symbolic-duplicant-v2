#!/usr/bin/env python3
PROGRAM = 'Symbolic Duplicant'
VERSION = 'v2.0'

import os
import sys

def set_enviorment_variables():
    """
    # * == set None for default value
    """
    os.environ['PROGRAM_NAME']         = PROGRAM
    os.environ['DATABASE_FILENAME']    = PROGRAM.replace(' ', '_') + '_database.sqlite'
    os.environ['DATABASE_FOLDER']      = '/home/plutonergy/Documents' # must exist, else: program-folder *
    os.environ['DATABASE_SUBFOLDER']   = PROGRAM # if preset, will be added to DATABASE_FOLDER *
    os.environ['TMP_DIR']              = '/mnt/ramdisk' # must exist, else: systems tmp-folder *
    os.environ['INI_FILENAME']         = 'settings.ini' # program-folder
    os.environ['VERSION']              = VERSION

def set_program_root_folder_in_eviorment():
    """
    also changes dir to __file__ directory
    """
    os.chdir(os.path.realpath(__file__)[0:os.path.realpath(__file__).rfind(os.sep)])
    INI_FILE_DIR = os.path.realpath(__file__)[0:os.path.realpath(__file__).rfind(os.sep) + 1]
    os.environ['INI_FILE_DIR'] = INI_FILE_DIR

set_enviorment_variables()
set_program_root_folder_in_eviorment()

from bscripts.main import MainDuplicant
from PyQt5 import QtWidgets

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainDuplicant()
    app.exec_()
