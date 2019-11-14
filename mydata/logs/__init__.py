"""
Custom logging for MyData allows logging to the Log view of MyData's
main window, and to ~/.MyData_debug_log.txt.  Logs can be submitted
via HTTP POST for analysis by developers / sys admins.
"""
# We want logger singleton to be lowercase, and we want logger.info,
# logger.warning etc. methods to be lowercase:
# pylint: disable=bare-except
import threading
import traceback
import logging
import os
import sys
import inspect

from io import StringIO

import requests
from requests.exceptions import RequestException
import six


class MyDataFormatter(logging.Formatter):
    """
    Can be used to handle logging messages coming from non-MyData modules
    which lack the extra attributes.
    """
    def format(self, record):
        """
        Overridden from logging.Formatter class
        """
        if not hasattr(record, 'module_name'):
            record.module_name = ''
        if not hasattr(record, 'function_name'):
            record.function_name = ''
        if not hasattr(record, 'line_number'):
            record.line_number = 0
        return super(MyDataFormatter, self).format(record)


class Logger():
    """
    Allows logger.debug(...), logger.info(...) etc. to write to MyData's
    Log window and to ~/.MyData_debug_log.txt
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, name):
        self.name = name
        self.logger_object = logging.getLogger(self.name)
        self.format_string = ""
        self.logger_output = None
        self.stream_handler = None
        self.file_handler = None
        self.level = logging.INFO
        self.configure_logger()
        if not hasattr(sys, "frozen"):
            self.app_root_dir = os.path.realpath(
                os.path.join(os.path.dirname(__file__), "..", ".."))

    def configure_logger(self):
        """
        Configure logger object
        """
        self.logger_object = logging.getLogger(self.name)
        self.logger_object.setLevel(self.level)

        self.format_string = \
            "%(asctime)s - %(module_name)s - %(line_number)d - " \
            "%(function_name)s - %(levelname)s - " \
            "%(message)s"

        # Send all log messages to a string.
        self.logger_output = StringIO()
        self.stream_handler = logging.StreamHandler(stream=self.logger_output)
        self.stream_handler.setLevel(self.level)
        self.stream_handler.setFormatter(MyDataFormatter(self.format_string))
        self.logger_object.addHandler(self.stream_handler)

        # Finally, send all log messages to a log file.
        if 'MYDATA_DEBUG_LOG_PATH' in os.environ:
            log_file_path = os.path.abspath(os.environ['MYDATA_DEBUG_LOG_PATH'])
            if os.path.isdir(log_file_path):
                log_file_path = os.path.join(log_file_path, ".MyData_debug_log.txt")
        else:
            log_file_path = os.path.join(
                os.path.expanduser("~"), ".MyData_debug_log.txt")
        self.file_handler = logging.FileHandler(log_file_path)
        self.file_handler.setLevel(self.level)
        self.file_handler.setFormatter(MyDataFormatter(self.format_string))
        self.logger_object.addHandler(self.file_handler)

    def debug(self, message):
        """
        Log a message with level logging.DEBUG
        """
        if self.level > logging.DEBUG:
            return
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)[1]
        if hasattr(sys, "frozen"):
            try:
                module_name = os.path.basename(outer_frames[1])
            except:
                module_name = outer_frames[1]
        else:
            module_name = os.path.relpath(outer_frames[1], self.app_root_dir)
        extra = {'module_name':  module_name,
                 'line_number': outer_frames[2],
                 'function_name': outer_frames[3]}
        self.logger_object.debug(message, extra=extra)

    def error(self, message):
        """
        Log a message with level logging.ERROR
        """
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)[1]
        if hasattr(sys, "frozen"):
            try:
                module_name = os.path.basename(outer_frames[1])
            except:
                module_name = outer_frames[1]
        else:
            module_name = os.path.relpath(outer_frames[1], self.app_root_dir)
        extra = {'module_name':  module_name,
                 'line_number': outer_frames[2],
                 'function_name': outer_frames[3]}
        self.logger_object.error(message, extra=extra)

    def warning(self, message):
        """
        Log a message with level logging.WARNING
        """
        if self.level > logging.WARNING:
            return
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)[1]
        if hasattr(sys, "frozen"):
            try:
                module_name = os.path.basename(outer_frames[1])
            except:
                module_name = outer_frames[1]
        else:
            module_name = os.path.relpath(outer_frames[1], self.app_root_dir)
        extra = {'module_name':  module_name,
                 'line_number': outer_frames[2],
                 'function_name': outer_frames[3]}
        self.logger_object.warning(message, extra=extra)

    def info(self, message):
        """
        Log a message with level logging.INFO
        """
        if self.level > logging.INFO:
            return
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)[1]
        if hasattr(sys, "frozen"):
            try:
                module_name = os.path.basename(outer_frames[1])
            except:
                module_name = outer_frames[1]
        else:
            module_name = os.path.relpath(outer_frames[1], self.app_root_dir)
        extra = {'module_name':  module_name,
                 'line_number': outer_frames[2],
                 'function_name': outer_frames[3]}
        self.logger_object.info(message, extra=extra)

    def exception(self, message):
        """
        Log a message and traceback for an exception
        """
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)[1]
        if hasattr(sys, "frozen"):
            try:
                module_name = os.path.basename(outer_frames[1])
            except:
                module_name = outer_frames[1]
        else:
            module_name = os.path.relpath(outer_frames[1], self.app_root_dir)
        extra = {'module_name':  module_name,
                 'line_number': outer_frames[2],
                 'function_name': outer_frames[3]}
        self.logger_object.exception(message, extra=extra)

    def testrun(self, message):
        # pylint: disable=no-self-use
        """
        Log to the test run window
        """
        sys.stderr.write("%s\n" % message)

    def get_value(self):
        """
        Return all logs sent to StringIO handler
        """
        self.stream_handler.flush()
        return self.logger_output.getvalue()

logger = Logger("MyData")  # pylint: disable=invalid-name
