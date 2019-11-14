"""
On Linux, running subprocess the usual way can be inefficient, due to
its use of os.fork().  So on Linux, we can use errand_boy to run our
subprocesses for us.
"""
import logging
import multiprocessing
import time
import uuid

# pylint: disable=import-error
from errand_boy.transports.unixsocket import UNIXSocketTransport

from .logs import logger


ERRAND_BOY_PROCESS = None
ERRAND_BOY_TRANSPORT = None

ERRAND_BOY_NUM_WORKERS = 10
ERRAND_BOY_MAX_ACCEPTS = 5000000
ERRAND_BOY_MAX_CHILD_TASKS = 100


def start_errand_boy():
    """
    Start errand boy.
    """
    errand_boy_logger = logging.getLogger("errand_boy.transports.unixsocket")
    errand_boy_logger.addHandler(logger.stream_handler)
    errand_boy_logger.addHandler(logger.file_handler)

    if ERRAND_BOY_PROCESS:
        stop_errand_boy()

    if not ERRAND_BOY_TRANSPORT:
        globals()['ERRAND_BOY_TRANSPORT'] = UNIXSocketTransport(
            socket_path='/tmp/errand-boy-%s' % str(uuid.uuid1()))

    def run_errand_boy_server():
        """
        Run the errand boy server.
        """
        ERRAND_BOY_TRANSPORT.run_server(
            pool_size=ERRAND_BOY_NUM_WORKERS,
            max_accepts=ERRAND_BOY_MAX_ACCEPTS,
            max_child_tasks=ERRAND_BOY_MAX_CHILD_TASKS
        )
    globals()['ERRAND_BOY_PROCESS'] = \
        multiprocessing.Process(target=run_errand_boy_server)
    ERRAND_BOY_PROCESS.start()
    count = 0
    while count < 10:
        time.sleep(0.1)
        try:
            ERRAND_BOY_TRANSPORT.run_cmd('test TRUE')
            break
        except IOError:
            pass


def stop_errand_boy():
    """
    Stop errand boy.
    """
    if ERRAND_BOY_PROCESS:
        ERRAND_BOY_PROCESS.terminate()
