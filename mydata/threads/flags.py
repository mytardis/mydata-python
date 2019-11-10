"""
Thread-safe flags
"""
import threading


class ThreadSafeFlags(object):
    """
    Thread-safe flags
    """
    def __init__(self):
        self._flags = dict()
        self._flags['scanning_folders'] = threading.Event()
        self._flags['test_run_running'] = threading.Event()
        self._flags['should_abort'] = threading.Event()

    @property
    def scanning_folders(self):
        """
        Returns True if MyData is currently scanning data folders.
        """
        return self._flags['scanning_folders'].isSet()

    @scanning_folders.setter
    def scanning_folders(self, value):
        """
        Records whether MyData is currently scanning data folders.
        """
        if value:
            self._flags['scanning_folders'].set()
        else:
            self._flags['scanning_folders'].clear()

    @property
    def test_run_running(self):
        """
        Called when the Test Run window is closed to determine
        whether the Test Run is still running.  If so, it will
        be aborted.  If not, we need to be careful to avoid
        aborting a real uploads run.
        """
        return self._flags['test_run_running'].isSet()

    @test_run_running.setter
    def test_run_running(self, value):
        """
        Records whether MyData is currently performing a test run.
        """
        if value:
            self._flags['test_run_running'].set()
        else:
            self._flags['test_run_running'].clear()

    @property
    def should_abort(self):
        """
        The most common reason for setting "should_abort" to True is when the
        user has requested aborting the data folder scans and/or datafile
        lookups (verifications) and/or uploads.

        It is also set when a critical failure / unhandled exception means
        that MyData needs to shut down the uploads before completion.

        When FoldersController's ShutDownUploadThreads finishes running, it
        will restore FLAGS.should_abort to its default value of False, but
        foldersController.canceled will remain set to True if the last session
        was canceled.  foldersController.canceled will be reset in
        FoldersController's InitializeStatusFlags method the next time we run
        the scans and uploads.
        """
        return self._flags['should_abort'].isSet()

    @should_abort.setter
    def should_abort(self, should_abort):
        """
        The user has requested aborting the data folder scans and/or
        datafile lookups (verifications) and/or uploads.
        """
        if should_abort:
            self._flags['should_abort'].set()
        else:
            self._flags['should_abort'].clear()

FLAGS = ThreadSafeFlags()
