"""
Queues used for consuming tasks for multi-threaded works
"""
import threading
from queue import Queue

LOOKUPS_QUEUE = Queue()
LOOKUP_THREADS = []


def lookup_worker():
    """Consume file lookup task(s) from the Lookups queue

    One worker per thread.

    By default, up to 4 lookup threads can run concurrently
    for looking up local files on the MyTardis server
    """
    while True:
        lookup_runnable = LOOKUPS_QUEUE.get()
        if not lookup_runnable:
            break
        lookup_runnable.lookup_datafile()


def init_lookup_threads():
    """Initialize lookup worker threads
    """
    from mydata.conf import settings

    for i in range(settings.advanced.max_lookup_threads):
        thread = threading.Thread(
            name="LookupThread-%d" % (i + 1), target=lookup_worker, daemon=True
        )
        LOOKUP_THREADS.append(thread)
        thread.start()
