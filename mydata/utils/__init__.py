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
import webbrowser

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


def safe_str(err, input_enc=sys.getfilesystemencoding(), output_enc='utf-8'):
    # pylint: disable=anomalous-unicode-escape-in-string
    """
    Safely return a string representation of an exception, possibly including
    a user-defined filesystem path.

    For an exception like this:

        except Exception as err:

    we can use str(err) to get a string representation of the error for
    logging (or for displaying in a message dialog).

    However in Python 2, Exception.__str__ can raise UnicodeDecodeError
    if the exception contains non-ASCII characters.  In MyData, these
    non-ASCII characters generally come from file or folder names which
    MyData is scanning, so they are expected to be encoded using
    sys.getfilesystemencoding().

    Given that str(err) can raise UnicodeDecodeError, we could use
    err.message, but it has been deprecated in some versions of Python 2
    and has been removed in Python 3.  In most cases, it can be replaced
    by err.args[0].  However in the case of IOError, the string
    representation is a combination of the args, e.g.

      "IOError: [Errno 5] foo: 'bar'"

    for IOError(5, "foo", "bar").

    SafeStr's default output encoding is utf-8, and before being encoded
    as utf-8, the Unicode string is normalized.  For example, suppose a
    filename contains the letter 'e' with an acute accent (é).  This could
    be represented by a single Unicode code point: u'\u00E9', or as the
    letter 'e' followed by the "combining acute accent", i.e. u'e\u0301'.
    We can normalize these as follows:

    >>> import unicodedata
    >>> unicodedata.normalize('NFC', u'\u00E9')
    u'\xe9'
    >>> unicodedata.normalize('NFC', u'e\u0301')
    u'\xe9'
    >>> u'\xe9' == u'\u00E9'
    True

    """
    try:
        return str(err)
    except UnicodeDecodeError:
        input_enc = input_enc or 'utf-8'
        if isinstance(err, (IOError, OSError)):
            decoded = "%s: [Errno %s] %s: '%s'" \
                % (type(err).__name__, err.errno,
                   err.strerror.decode(input_enc),
                   err.filename.decode(input_enc))
        else:
            decoded = err.args[0].decode(input_enc)
    normalized = unicodedata.normalize('NFC', decoded)
    return normalized.encode(output_enc)


def compare(obj1, obj2):
    """
    Compare the two objects obj1 and obj2 and return an integer according
    to the outcome. The return value is negative if obj1 < obj2, zero if
    obj1 == obj2 and strictly positive if obj1 > obj2.
    """
    return (obj1 > obj2) - (obj1 < obj2)


def open_url(url, new=0, autoraise=True):
    """
    Open URL in web browser or just check URL is accessible if running tests.
    """
    webbrowser.open(url, new, autoraise)


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


def initialize_trusted_certs_path():
    """
    Tell the requests module where to find the CA (Certificate Authority)
    certificates bundled with MyData.
    """
    if hasattr(sys, "frozen"):
        if sys.platform.startswith("darwin"):
            cert_path = os.path.realpath(os.path.join(
                os.path.dirname(sys.executable), '..', 'Resources'))
        else:
            cert_path = os.path.dirname(sys.executable)
        os.environ['REQUESTS_CA_BUNDLE'] = \
            os.path.join(cert_path, 'cacert.pem')


def gnome_shell_is_running():
    """
    Check if the GNOME Shell desktop environment is running.
    Helper function for CheckIfSystemTrayFunctionalityMissing.
    """
    for pid in psutil.pids():
        try:
            proc = psutil.Process(pid)
            if 'gnome-shell' in proc.name():
                return True
        except psutil.NoSuchProcess:
            pass
    return False


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
