"""
Model class for the settings not displayed in the settings dialog,
but accessible in MyData.cfg, or in the case of "locked", visible in the
settings dialog, but not specific to any one tab view.

Also includes miscellaneous functionality which needed to be moved out of
the main settings model module (model.py) to prevent cyclic imports.
"""
import sys

from .base import BaseSettingsModel


class LastSettingsUpdateTrigger():
    """
    Enumerated data type encapsulating the trigger for the last change to
    the settings.

    This is used to determine whether settings validation is required.

    If the user opens the settings dialog, and clicks OK, validation is
    performed automatically, so there is no need to validate settings
    again at the beginning of a scan-folders-and-upload task commenced
    shortly after closing the settings dialog.

    However, if MyData finds a MyData.cfg on disk when it launches, and
    then the user clicks the "Upload" button without opening the settings
    dialog first, then we do need to validate settings.
    """
    # The last update to settings came from reading MyData.cfg from disk:
    READ_FROM_DISK = 0
    # The last update to settings came from the settings dialog:
    UI_RESPONSE = 1


class MiscellaneousSettingsModel(BaseSettingsModel):
    """
    Model class for the settings not displayed in the settings dialog,
    but accessible in MyData.cfg, or in the case of "locked", visible in the
    settings dialog, but not specific to any one tab view.
    """
    def __init__(self):
        super(MiscellaneousSettingsModel, self).__init__()

        # Saved in MyData.cfg:
        self.mydata_config = dict()

        self.fields = [
            'locked',
            'uuid',
            'verification_delay',
            'max_verification_threads',
            'fake_md5_sum',
            'cipher',
            'progress_poll_interval',
            'cache_datafile_lookups',
            'connection_timeout'
        ]

        self.default = dict(
            locked=False,
            uuid=None,
            verification_delay=3.0,
            max_verification_threads=5,
            fake_md5_sum=False,
            cipher="aes128-ctr",
            progress_poll_interval=1.0,
            cache_datafile_lookups=True,
            connection_timeout=10.0)

        # Settings determined from command-line arguments of the
        # MyData binary or the run.py entry point which are
        # not saved in MyData.cfg:
        self.autoexit = False

    @property
    def locked(self):
        """
        Settings Dialog's Lock/Unlock button

        Return True if settings are locked
        """
        return self.mydata_config['locked']

    @locked.setter
    def locked(self, locked):
        """
        Settings Dialog's Lock/Unlock button

        Set this to True to lock settings
        """
        self.mydata_config['locked'] = locked

    @property
    def uuid(self):
        """
        Get this MyData instance's unique ID
        """
        return self.mydata_config['uuid']

    @uuid.setter
    def uuid(self, uuid):
        """
        Set this MyData instance's unique ID
        """
        self.mydata_config['uuid'] = uuid

    @property
    def fake_md5_sum(self):
        """
        Whether to use a fake MD5 sum to save time.
        It can be set later via the MyTardis API.
        Until it is set properly, the file won't be
        verified on MyTardis.
        """
        return self.mydata_config['fake_md5_sum']

    @property
    def verification_delay(self):
        """
        Upon a successful upload, MyData will request verification
        after a short delay, defaulting to 3 seconds:

        :return: the delay in seconds
        :rtype: float
        """
        return self.mydata_config['verification_delay']

    @property
    def max_verification_threads(self):
        """
        Return the maximum number of concurrent DataFile lookups
        """
        return int(self.mydata_config['max_verification_threads'])

    @max_verification_threads.setter
    def max_verification_threads(self, max_verification_threads):
        """
        Set the maximum number of concurrent DataFile lookups
        """
        self.mydata_config['max_verification_threads'] = max_verification_threads

    @staticmethod
    def get_fake_md5sum():
        """
        The fake MD5 sum to use when self.FakeMd5Sum()
        is True.
        """
        return "00000000000000000000000000000000"

    @property
    def cipher(self):
        """
        SSH Cipher for SCP uploads.
        """
        return self.mydata_config['cipher']

    @property
    def cipher_options(self):
        """
        SSH Cipher Options for SCP uploads.
        """
        return ["-c", self.mydata_config['cipher']]

    @property
    def progress_poll_interval(self):
        """
        Upload progress is queried periodically via the MyTardis API.
        Returns the interval in seconds between RESTful progress queries.

        :return: the interval in seconds
        :rtype: float
        """
        return self.mydata_config['progress_poll_interval']

    @property
    def cache_datafile_lookups(self):
        """
        Returns True if MyData will cache local paths and dataset IDs of
        datafiles which have been previously found to be verified on MyTardis.
        """
        return self.mydata_config['cache_datafile_lookups']

    @cache_datafile_lookups.setter
    def cache_datafile_lookups(self, cache_datafile_lookups):
        """
        Set this to True if MyData should cache local paths and dataset IDs of
        datafiles which have been previously found to be verified on MyTardis.
        """
        self.mydata_config['cache_datafile_lookups'] = cache_datafile_lookups

    @property
    def connection_timeout(self):
        """
        Timeout (in seconds) used for HTTP responses and SSH connections

        :return: the timeout in seconds
        :rtype: float
        """
        return self.mydata_config['connection_timeout']

    @connection_timeout.setter
    def connection_timeout(self, connection_timeout):
        """
        Timeout (in seconds) used for HTTP responses and SSH connections

        :param connection_timeout: the timeout in seconds
        :type connection_timeout: float
        """
        self.mydata_config['connection_timeout'] = connection_timeout

    def set_default_for_field(self, field):
        """
        Set default value for one field.
        """
        self.mydata_config[field] = self.default[field]
        if field == 'cipher':
            if sys.platform.startswith("win"):
                self.mydata_config['cipher'] = \
                    "aes128-gcm@openssh.com,aes128-ctr"
            else:
                # On Mac/Linux, we don't bundle SSH binaries, we
                # just use the installed SSH version, which might
                # be too old to support aes128-gcm@openssh.com
                self.mydata_config['cipher'] = "aes128-ctr"
