"""
Model class for a datafile upload, which appears as one row in
the Uploads view of MyData's main window.
"""
# pylint: disable=broad-except
import os
import sys
import signal
import traceback

from ..logs import logger
from ..utils import human_readable_size_string


class UploadStatus:
    """
    Enumerated data type.

    This is used to update the status seen in the Uploads view.
    Stored in an Upload model instance's status attribute, this
    field
    """

    # pylint: disable=invalid-name
    NOT_STARTED = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3
    CANCELED = 4


UPLOAD_STATUS = ["Not Started", "In Progress", "Completed", "Failed", "Canceled"]


class UploadMethod:
    """
    Enumerated data type for upload methods
    """

    # pylint: disable=invalid-name
    MULTIPART_POST = 0
    SCP = 1
    SFTP = 2
    SSH2 = 3
    LOCAL_COPY = 3  # includes copying to mounted file share


def add_uploader_info(datafile_dict):
    """
    To identify the approved storage box for the upload, the
    mytardis-app-mydata app needs to be able to identify the
    uploader registration request, which can be done with the
    Uploader UUID and the ~/.ssh/MyData.pub key's fingerprint.
    """
    from mydata.conf import settings

    datafile_dict["uploader_uuid"] = settings.miscellaneous.uuid
    datafile_dict[
        "requester_key_fingerprint"
    ] = settings.uploader.ssh_key_pair.fingerprint
    return datafile_dict


class Upload:
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
        self.subdirectory = folder.get_datafile_directory(datafile_index)
        self.filename = folder.get_datafile_name(datafile_index)
        # Human-readable string displayed in data view:
        self.filesize_string = ""

        self.bytes_uploaded = 0
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

        self.start_time = None
        # The latest time at which upload progress has been measured:
        self.latest_time = None

        # After the file is uploaded, MyData will request verification
        # after a short delay.  During that delay, the countdown timer
        # will be stored in the Upload instance so that it can be canceled
        # if necessary:
        self.verification_timer = None

    def set_latest_time(self, latest_time):
        """
        Set the latest time at which this upload is/was still progressing.
        """
        self.latest_time = latest_time
        if self.bytes_uploaded and self.latest_time:
            elapsed_time = self.latest_time - self.start_time
            if elapsed_time.total_seconds():
                speed_mbs = (
                    float(self.bytes_uploaded)
                    / 1000000.0
                    / elapsed_time.total_seconds()
                )
                if speed_mbs >= 1.0:
                    self.speed = "%3.1f MB/s" % speed_mbs
                else:
                    self.speed = "%3.1f KB/s" % (speed_mbs * 1000.0)

    def get_value_for_key(self, key):
        """
        Return value of field from the Upload instance
        to display in the Uploads view
        """
        return getattr(self, key)

    def get_relative_path_to_upload(self):
        """
        Get the local path to this Upload instance's file,
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
                except Exception:
                    logger.error(traceback.format_exc())
            if self.buffered_reader is not None:
                self.buffered_reader.close()
                logger.debug(
                    'Closed buffered reader for "'
                    + self.get_relative_path_to_upload()
                    + '".'
                )
            if self.scp_upload_process_pid:
                if sys.platform.startswith("win"):
                    os.kill(self.scp_upload_process_pid, signal.SIGABRT)
                else:
                    os.kill(self.scp_upload_process_pid, signal.SIGKILL)  # pylint: disable=no-member
        except Exception:
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
