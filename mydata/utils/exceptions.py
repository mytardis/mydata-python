"""
Custom exceptions to raise within MyData.
"""


class DuplicateKey(Exception):
    """
    Duplicate key exception.
    """


class MultipleObjectsReturned(Exception):
    """
    Multiple objects returned exception.
    """


class SshException(Exception):
    """
    SSH exception.
    """

    def __init__(self, message, returncode=None):
        super().__init__(message)
        self.returncode = returncode


class ScpException(SshException):
    """
    SCP exception.
    """

    def __init__(self, message, command=None, returncode=None):
        super().__init__(message)
        self.command = command
        self.returncode = returncode


class NoActiveNetworkInterface(Exception):
    """
    No active network interface exception.
    """


class BrokenPipe(Exception):
    """
    Broken pipe exception.
    """


class PrivateKeyDoesNotExist(Exception):
    """
    Private key does not exist exception.
    """


class InvalidFolderStructure(Exception):
    """
    Invalid folder structure exception.
    """


class MissingMyDataAppOnMyTardisServer(Exception):
    """
    Missing MyData app on MyTardis server exception.
    """


class MissingMyDataReplicaApiEndpoint(Exception):
    """
    Missing /api/v1/mydata_replica/ endpoint on MyTardis server exception.
    """


class NoApprovedStorageBox(Exception):
    """
    No approved storage box was specified in the Uploader Registration Request
    """


class StorageBoxAttributeNotFound(Exception):
    """
    Storage box attribute not found exception.
    """

    def __init__(self, storageBox, key):
        message = "Key '%s' not found in attributes for storage box '%s'" % (
            key,
            storageBox.name,
        )
        self.key = key
        super().__init__(message)


class StorageBoxOptionNotFound(Exception):
    """
    Storage box option not found exception.
    """

    def __init__(self, storageBox, key):
        message = "Key '%s' not found in options for storage box '%s'" % (
            key,
            storageBox.name,
        )
        super().__init__(message)


class UserAborted(Exception):
    """
    User aborted by pressing the Stop button
    on the main window's toolbar.
    """


class InvalidSettings(Exception):
    """
    Invalid settings were found by
    mydata.models.settings.validation.ValidateSettings
    """

    def __init__(self, message, field="", suggestion=None):
        self.field = field
        self.suggestion = suggestion
        super().__init__(message)
