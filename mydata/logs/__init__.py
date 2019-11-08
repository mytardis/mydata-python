"""
Custom logging for MyData allows logging to the Log view of MyData's
main window, and to ~/.MyData_debug_log.txt.  Logs can be submitted
via HTTP POST for analysis by developers / sys admins.
"""
# We want logger singleton to be lowercase, and we want logger.info,
# logger.warning etc. methods to be lowercase:
# pylint: disable=invalid-name
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
        if not hasattr(record, 'moduleName'):
            record.moduleName = ''
        if not hasattr(record, 'functionName'):
            record.functionName = ''
        if not hasattr(record, 'currentThreadName'):
            record.currentThreadName = ''
        if not hasattr(record, 'lineNumber'):
            record.lineNumber = 0
        return super(MyDataFormatter, self).format(record)


class Logger():
    """
    Allows logger.debug(...), logger.info(...) etc. to write to MyData's
    Log window and to ~/.MyData_debug_log.txt
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, name):
        self.name = name
        self.loggerObject = logging.getLogger(self.name)
        self.formatString = ""
        self.loggerOutput = None
        self.streamHandler = None
        self.fileHandler = None
        self.level = logging.INFO
        self.ConfigureLogger()
        if not hasattr(sys, "frozen"):
            self.appRootDir = os.path.realpath(
                os.path.join(os.path.dirname(__file__), "..", ".."))
        self.logTextCtrl = None
        self.pleaseContactMe = False
        self.contactName = ""
        self.contactEmail = ""
        self.comments = ""

    def ConfigureLogger(self):
        """
        Configure logger object
        """
        self.loggerObject = logging.getLogger(self.name)
        self.loggerObject.setLevel(self.level)

        self.formatString = \
            "%(asctime)s - %(moduleName)s - %(lineNumber)d - " \
            "%(functionName)s - %(currentThreadName)s - %(levelname)s - " \
            "%(message)s"

        # Send all log messages to a string.
        self.loggerOutput = StringIO()
        self.streamHandler = logging.StreamHandler(stream=self.loggerOutput)
        self.streamHandler.setLevel(self.level)
        self.streamHandler.setFormatter(MyDataFormatter(self.formatString))
        self.loggerObject.addHandler(self.streamHandler)

        # Finally, send all log messages to a log file.
        if 'MYDATA_DEBUG_LOG_PATH' in os.environ:
            logFilePath = os.path.abspath(os.environ['MYDATA_DEBUG_LOG_PATH'])
            if os.path.isdir(logFilePath):
                logFilePath = os.path.join(logFilePath,
                                           ".MyData_debug_log.txt")
        else:
            logFilePath = os.path.join(os.path.expanduser("~"),
                                       ".MyData_debug_log.txt")
        self.fileHandler = logging.FileHandler(logFilePath)
        self.fileHandler.setLevel(self.level)
        self.fileHandler.setFormatter(MyDataFormatter(self.formatString))
        self.loggerObject.addHandler(self.fileHandler)

    def GetLevel(self):
        """
        Returns the logging level, e.g. logging.DEBUG
        """
        return self.level

    def SetLevel(self, level):
        """
        Sets the logging level, e.g. logging.DEBUG
        """
        self.level = level
        self.loggerObject.setLevel(self.level)
        for handler in self.loggerObject.handlers:
            handler.setLevel(self.level)

    def debug(self, message):
        """
        Log a message with level logging.DEBUG
        """
        if self.level > logging.DEBUG:
            return
        frame = inspect.currentframe()
        outerFrames = inspect.getouterframes(frame)[1]
        if hasattr(sys, "frozen"):
            try:
                moduleName = os.path.basename(outerFrames[1])
            except:
                moduleName = outerFrames[1]
        else:
            moduleName = os.path.relpath(outerFrames[1], self.appRootDir)
        extra = {'moduleName':  moduleName,
                 'lineNumber': outerFrames[2],
                 'functionName': outerFrames[3],
                 'currentThreadName': threading.current_thread().name}
        self.loggerObject.debug(message, extra=extra)

    def error(self, message):
        """
        Log a message with level logging.ERROR
        """
        frame = inspect.currentframe()
        outerFrames = inspect.getouterframes(frame)[1]
        if hasattr(sys, "frozen"):
            try:
                moduleName = os.path.basename(outerFrames[1])
            except:
                moduleName = outerFrames[1]
        else:
            moduleName = os.path.relpath(outerFrames[1], self.appRootDir)
        extra = {'moduleName':  moduleName,
                 'lineNumber': outerFrames[2],
                 'functionName': outerFrames[3],
                 'currentThreadName': threading.current_thread().name}
        self.loggerObject.error(message, extra=extra)

    def warning(self, message):
        """
        Log a message with level logging.WARNING
        """
        if self.level > logging.WARNING:
            return
        frame = inspect.currentframe()
        outerFrames = inspect.getouterframes(frame)[1]
        if hasattr(sys, "frozen"):
            try:
                moduleName = os.path.basename(outerFrames[1])
            except:
                moduleName = outerFrames[1]
        else:
            moduleName = os.path.relpath(outerFrames[1], self.appRootDir)
        extra = {'moduleName':  moduleName,
                 'lineNumber': outerFrames[2],
                 'functionName': outerFrames[3],
                 'currentThreadName': threading.current_thread().name}
        self.loggerObject.warning(message, extra=extra)

    def info(self, message):
        """
        Log a message with level logging.INFO
        """
        if self.level > logging.INFO:
            return
        frame = inspect.currentframe()
        outerFrames = inspect.getouterframes(frame)[1]
        if hasattr(sys, "frozen"):
            try:
                moduleName = os.path.basename(outerFrames[1])
            except:
                moduleName = outerFrames[1]
        else:
            moduleName = os.path.relpath(outerFrames[1], self.appRootDir)
        extra = {'moduleName':  moduleName,
                 'lineNumber': outerFrames[2],
                 'functionName': outerFrames[3],
                 'currentThreadName': threading.current_thread().name}
        self.loggerObject.info(message, extra=extra)

    def exception(self, message):
        """
        Log a message and traceback for an exception
        """
        frame = inspect.currentframe()
        outerFrames = inspect.getouterframes(frame)[1]
        if hasattr(sys, "frozen"):
            try:
                moduleName = os.path.basename(outerFrames[1])
            except:
                moduleName = outerFrames[1]
        else:
            moduleName = os.path.relpath(outerFrames[1], self.appRootDir)
        extra = {'moduleName':  moduleName,
                 'lineNumber': outerFrames[2],
                 'functionName': outerFrames[3],
                 'currentThreadName': threading.current_thread().name}
        self.loggerObject.exception(message, extra=extra)

    def testrun(self, message):
        # pylint: disable=no-self-use
        """
        Log to the test run window
        """
        sys.stderr.write("%s\n" % message)

    def GetValue(self):
        """
        Return all logs sent to StringIO handler
        """
        self.streamHandler.flush()
        return self.loggerOutput.getvalue()

logger = Logger("MyData")
