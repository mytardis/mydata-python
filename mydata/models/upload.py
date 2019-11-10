"""
Model class for a datafile upload, which appears as one row in
the Uploads view of MyData's main window.
"""
# pylint: disable=bare-except
import os
import sys
import signal
import traceback

from ..logs import logger
from ..utils import human_readable_size_string


class UploadStatus():
    """
    Enumerated data type.

    This is used to update the status seen in the Uploads view.
    Stored in an UploadModel instance's status attribute, this
    field
    """
    # pylint: disable=invalid-name
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3
    PAUSED = 4
    CANCELED = 5


class UploadModel():
    """
    Model class for a datafile upload, which appears as one row in
    the Uploads view of MyData's main window.
    """
    # pylint: disable=too-many-public-methods
    # pylint: disable=too-many-instance-attributes
    def __init__(self, folder, datafile_index):
        self.datafile_index = datafile_index
        self.datafile_id = None
        self.folder_name = folder.name
        self.subdirectory = folder.GetDataFileDirectory(datafile_index)
        self.filename = folder.GetDataFileName(datafile_index)
        # Human-readable string displayed in data view:
        self.filesize_string = ""

        # Number of bytes uploaded (used to render progress bar):
        self.bytes_uploaded = 0
        self.progress = 0  # Percentage used to render progress bar
        self.status = UploadStatus.NOT_STARTED
        self.message = ""
        self.speed = ""
        self.traceback = None
        self._file_size = 0  # File size long integer in bytes
        self.canceled = False
        self.retries = 0

        # Only used with UploadMethod.HTTP_POST:
        self.buffered_reader = None

        # Only used with UploadMethod.VIA_STAGING:
        self.scp_upload_process_pid = None
        self._existing_unverified_datafile = None
        # The DataFileObject ID, also known as the replica ID:
        self.dfo_id = None
        # Number of bytes previously uploaded, or None if the file is not yet
        # on the staging area:
        self.bytes_uploaded_previously = None

        self.start_time = None
        # The latest time at which upload progress has been measured:
        self.latest_time = None

        # After the file is uploaded, MyData will request verification
        # after a short delay.  During that delay, the countdown timer
        # will be stored in the UploadModel so that it can be canceled
        # if necessary:
        self.verification_timer = None

    def set_bytes_uploaded(self, bytes_uploaded):
        """
        Set the number of bytes uploaded and update
        the elapsed time and upload speed.
        """
        self.bytes_uploaded = bytes_uploaded
        if self.bytes_uploaded and self.latest_time:
            elapsed_time = self.latest_time - self.start_time
            if elapsed_time.total_seconds():
                speed_mbs = (float(self.bytes_uploaded) / 1000000.0 /
                             elapsed_time.total_seconds())
                if speed_mbs >= 1.0:
                    self.speed = "%3.1f MB/s" % speed_mbs
                else:
                    self.speed = "%3.1f KB/s" % (speed_mbs * 1000.0)

    def set_progress(self, progress):
        """
        Set upload progress and update UploadStatus.
        """
        self.progress = progress
        if 0 < progress < 100:
            self.status = UploadStatus.IN_PROGRESS

    def set_latest_time(self, latest_time):
        """
        Set the latest time at which this upload is/was still progressing.

        This is updated while the upload is still in progress, so we can
        provide real time upload speed estimates.
        """
        self.latest_time = latest_time
        if self.bytes_uploaded and self.latest_time:
            elapsed_time = self.latest_time - self.start_time
            if elapsed_time.total_seconds():
                speed_mbs = (float(self.bytes_uploaded) / 1000000.0 /
                             elapsed_time.total_seconds())
                if speed_mbs >= 1.0:
                    self.speed = "%3.1f MB/s" % speed_mbs
                else:
                    self.speed = "%3.1f KB/s" % (speed_mbs * 1000.0)

    def get_value_for_key(self, key):
        """
        Return value of field from the UploadModel
        to display in the Uploads view
        """
        return getattr(self, key)

    def get_relative_path_to_upload(self):
        """
        Get the local path to this UploadModel's file,
        relative to the dataset folder
        """
        if self.subdirectory != "":
            relpath = os.path.join(self.subdirectory, self.filename)
        else:
            relpath = self.filename
        return relpath

    def cancel(self):
        """
        Abort this upload
        """
        try:
            self.canceled = True
            self.status = UploadStatus.CANCELED
            if self.verification_timer:
                try:
                    self.verification_timer.cancel()
                except:
                    logger.error(traceback.format_exc())
            if self.buffered_reader is not None:
                self.buffered_reader.close()
                logger.debug("Closed buffered reader for \"" +
                             self.get_relative_path_to_upload() +
                             "\".")
            if self.scp_upload_process_pid:
                if sys.platform.startswith("win"):
                    os.kill(self.scp_upload_process_pid, signal.SIGABRT)
                else:
                    os.kill(self.scp_upload_process_pid, signal.SIGKILL)
        except:
            logger.warning(traceback.format_exc())

    @property
    def file_size(self):
        """
        Return the file-to-be-uploaded's file size
        """
        return self._file_size

    @file_size.setter
    def file_size(self, file_size):
        """
        Record the file-to-be-uploaded's file size and update the
        human-readable string version of the file size
        """
        self._file_size = file_size
        self.filesize_string = human_readable_size_string(self._file_size)

    @property
    def existing_unverified_datafile(self):
        """
        Return the existing unverified DataFile record (if any)
        associated with this upload
        """
        return self._existing_unverified_datafile

    @existing_unverified_datafile.setter
    def existing_unverified_datafile(self, existing_unverified_datafile):
        """
        Record an existing unverified DataFile
        """
        self._existing_unverified_datafile = existing_unverified_datafile
        if self._existing_unverified_datafile:
            self.datafile_id = self._existing_unverified_datafile.datafileId
            replicas = self._existing_unverified_datafile.replicas
            if len(replicas) == 1:
                self.dfo_id = replicas[0].dfo_id
