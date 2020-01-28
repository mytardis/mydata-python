"""
Model class for settings not displayed in the settings dialog of the
MyData GUI but accessible in MyData.cfg.  The MyData CLI retains the
MyData GUI code's separation of settings in General / Advanced / Miscellaneous etc.
even though it doesn't have a Settings Dialog.

Also includes miscellaneous functionality which needed to be moved out of
the main settings model module (model.py) to prevent cyclic imports.
"""
import sys

from .base import BaseSettings


class MiscellaneousSettings(BaseSettings):
    """
    Model class for settings not displayed in the settings dialog of the
    MyData GUI but accessible in MyData.cfg.  The MyData CLI retains the
    MyData GUI code's separation of settings in General / Advanced / Miscellaneous etc.
    even though it doesn't have a Settings Dialog.
    """

    def __init__(self):
        super(MiscellaneousSettings, self).__init__()

        # Saved in MyData.cfg:
        self.mydata_config = dict()

        self.fields = [
            "uuid",
            "verification_delay",
            "max_verification_threads",
            "fake_md5_sum",
            "cipher",
            "cache_datafile_lookups",
            "connection_timeout",
        ]

        self.default = dict(
            uuid=None,
            verification_delay=3.0,
            max_verification_threads=5,
            fake_md5_sum=False,
            cipher="aes128-ctr",
            cache_datafile_lookups=True,
            connection_timeout=10.0,
        )

    @property
    def uuid(self):
        """
        Get this MyData instance's unique ID
        """
        return self.mydata_config["uuid"]

    @uuid.setter
    def uuid(self, uuid):
        """
        Set this MyData instance's unique ID
        """
        self.mydata_config["uuid"] = uuid

    @property
    def fake_md5_sum(self):
        """
        Whether to use a fake MD5 sum to save time.
        It can be set later via the MyTardis API.
        Until it is set properly, the file won't be
        verified on MyTardis.
        """
        return self.mydata_config["fake_md5_sum"]

    @property
    def verification_delay(self):
        """
        Upon a successful upload, MyData will request verification
        after a short delay, defaulting to 3 seconds:

        :return: the delay in seconds
        :rtype: float
        """
        return self.mydata_config["verification_delay"]

    @property
    def max_verification_threads(self):
        """
        Return the maximum number of concurrent DataFile lookups
        """
        return int(self.mydata_config["max_verification_threads"])

    @max_verification_threads.setter
    def max_verification_threads(self, max_verification_threads):
        """
        Set the maximum number of concurrent DataFile lookups
        """
        self.mydata_config["max_verification_threads"] = max_verification_threads

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
        return self.mydata_config["cipher"]

    @property
    def cipher_options(self):
        """
        SSH Cipher Options for SCP uploads.
        """
        return ["-c", self.mydata_config["cipher"]]

    @property
    def cache_datafile_lookups(self):
        """
        Returns True if MyData will cache local paths and dataset IDs of
        datafiles which have been previously found to be verified on MyTardis.
        """
        return self.mydata_config["cache_datafile_lookups"]

    @cache_datafile_lookups.setter
    def cache_datafile_lookups(self, cache_datafile_lookups):
        """
        Set this to True if MyData should cache local paths and dataset IDs of
        datafiles which have been previously found to be verified on MyTardis.
        """
        self.mydata_config["cache_datafile_lookups"] = cache_datafile_lookups

    @property
    def connection_timeout(self):
        """
        Timeout (in seconds) used for HTTP responses and SSH connections

        :return: the timeout in seconds
        :rtype: float
        """
        return self.mydata_config["connection_timeout"]

    @connection_timeout.setter
    def connection_timeout(self, connection_timeout):
        """
        Timeout (in seconds) used for HTTP responses and SSH connections

        :param connection_timeout: the timeout in seconds
        :type connection_timeout: float
        """
        self.mydata_config["connection_timeout"] = connection_timeout

    def set_default_for_field(self, field):
        """
        Set default value for one field.
        """
        self.mydata_config[field] = self.default[field]
        if field == "cipher":
            if sys.platform.startswith("win"):
                self.mydata_config["cipher"] = "aes128-gcm@openssh.com,aes128-ctr"
            else:
                # On Mac/Linux, we don't bundle SSH binaries, we
                # just use the installed SSH version, which might
                # be too old to support aes128-gcm@openssh.com
                self.mydata_config["cipher"] = "aes128-ctr"
