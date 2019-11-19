# -*- coding: utf-8 -*-
"""
Miscellaneous utility functions.
"""
# pylint: disable=bare-except
import os
import sys
import subprocess
import traceback
import unicodedata

import appdirs
import psutil

from ..constants import APPNAME, APPAUTHOR
from ..logs import logger
from ..threads.locks import LOCKS


def pid_is_running(pid):
    """
    Check if a process with PID pid is running.
    """
    try:
        proc = psutil.Process(int(pid))
        if proc.status() == psutil.STATUS_DEAD:
            return False
        if proc.status() == psutil.STATUS_ZOMBIE:
            return False
        return True  # Assume other status are valid
    except psutil.NoSuchProcess:
        return False


def human_readable_size_string(num):
    """
    Returns human-readable string.
    """
    for unit in ['bytes', 'KB', 'MB', 'GB']:
        if -1024.0 < num < 1024.0:
            return "%3.1f %s" % (num, unit)
        num /= 1024.0
    return "%3.1f %s" % (num, 'TB')


def bytes_to_human(num_bytes):
    """
    Returns human-readable string.
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for index, symbol in enumerate(symbols):
        prefix[symbol] = 1 << (index + 1) * 10
    for symbol in reversed(symbols):
        if num_bytes >= prefix[symbol]:
            value = float(num_bytes) / prefix[symbol]
            return '%.1f%s' % (value, symbol)
    return "%sB" % num_bytes


def create_config_path_if_necessary():
    """
    Create path for saving MyData.cfg if it doesn't already exist.
    """
    if sys.platform.startswith("win"):
        # We use a setup wizard on Windows which runs with admin
        # privileges, so we can ensure that the appdir_path below,
        # i.e. C:\ProgramData\Monash University\MyData\ is
        # writeable by all users.
        appdir_path = appdirs.site_config_dir(APPNAME, APPAUTHOR)
    else:
        # On Mac, we currently use a DMG drag-and-drop installation, so
        # we can't create a system-wide MyData.cfg writeable by all users.
        appdir_path = appdirs.user_data_dir(APPNAME, APPAUTHOR)
    if not os.path.exists(appdir_path):
        os.makedirs(appdir_path)
    return appdir_path


def mydata_install_location():
    """
    Return MyData install location
    """
    if hasattr(sys, 'frozen'):
        return os.path.dirname(sys.executable)
    try:
        return os.path.realpath(
            os.path.join(os.path.dirname(__file__), "..", ".."))
    except:
        return os.getcwd()
