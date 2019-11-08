"""
mydata/events/stop.py

This module contains methods relating to stopping MyData's scan-and-upload
processes.
"""
from ..threads.flags import FLAGS
from ..utils.exceptions import UserAborted


def ShouldCancelUpload(uploadModel):
    """Return True if the upload should be canceled
    """
    if FLAGS.shouldAbort or uploadModel.canceled:
        return True

    # This code would only run in tests where a scheduled progress query
    # from one test attempts to run in a subsequent test, but the subsequent
    # test doesn't create a folders controller instance.  (See the use of
    # threading.Timer in mydata.utils.progress.)
    return True


def RaiseExceptionIfUserAborted(setStatusMessage=None):
    """Check if user has aborted / canceled and if so, raise an exception

    A function accepting a status message string argument can be
    supplied which will be called before the exception is raised.
    """
    if FLAGS.shouldAbort:
        message = "Canceled by user"
        if setStatusMessage:
            setStatusMessage(message)
        raise UserAborted(message)
