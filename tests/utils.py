"""
tests/utils.py
"""
import socket
import sys


def unload_modules():
    """Unload modules - called at the end of a test

    Required because MyData makes use of singletons,
    in particular settings which makes sense in a normal
    MyData run but not in a series of unit tests.
    """
    sys_modules = list(sys.modules.keys())
    for module in sys_modules:
        if "mydata" in module:
            del sys.modules[module]


def subtract(str1, str2):
    """
    Subtract strings, e.g. "foobar" - "foo" = "bar"
    to isolate recently added logs from total log history.
    """
    if not str2:
        return str1
    return "".join(str1.rsplit(str2))


def get_ephemeral_port():
    """
    Return an unused ephemeral port.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port
