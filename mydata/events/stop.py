"""
mydata/events/stop.py

This module contains methods relating to stopping MyData's scan-and-upload
processes.
"""
from ..threads.flags import FLAGS
from ..utils.exceptions import UserAborted


def should_cancel_upload(upload):
    """Return True if the upload should be canceled
    """
    return FLAGS.should_abort or upload.canceled


def raise_exception_if_user_aborted(set_status_message=None):
    """Check if user has aborted / canceled and if so, raise an exception

    A function accepting a status message string argument can be
    supplied which will be called before the exception is raised.
    """
    if FLAGS.should_abort:
        message = "Canceled by user"
        if set_status_message:
            set_status_message(message)
        raise UserAborted(message)
