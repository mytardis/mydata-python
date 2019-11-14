"""
Locks for thread synchronization
"""
import threading

LOCK_NAMES = [
    'scanning_folders', 'create_uploader', 'request_staging_access',
    'update_cache', 'close_cache']

class ThreadingLocks():
    """
    Locks for thread synchronization.

    Each lock can be accessed as LOCKS.[lock_name] e.g. LOCKS.update_cache
    where LOCKS is the singleton instance of the ThreadingLocks class.

    Usage:

        from .threads.locks import LOCKS
        with LOCKS.update_cache:
            UpdateCache()
    """
    def __init__(self):
        """
        We will only define one instance of the ThreadingLocks class,
        called 'LOCKS', so the 'self' in the lambda expression will
        always be the LOCKS instance.
        """
        self._locks = dict()
        for lock_name in LOCK_NAMES:
            self._locks[lock_name] = threading.Lock()
            setattr(ThreadingLocks, lock_name,
                    property(lambda self, key=lock_name: self._locks[key]))


LOCKS = ThreadingLocks()
