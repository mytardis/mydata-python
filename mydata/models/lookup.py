"""
Models for datafile lookup / verification.
"""


class LookupStatus:
    """
    Enumerated data type for lookup states.
    """

    NOT_STARTED = 0

    IN_PROGRESS = 1

    # Not found on MyTardis, need to upload this file:
    NOT_FOUND = 2

    # Found on MyTardis (and verified), no need to upload this file:
    FOUND_VERIFIED = 3

    # Found unverified DataFile record, but we're using POST, not staged
    # uploads, so we can't retry without triggering a Duplicate Key error:
    FOUND_UNVERIFIED_UNSTAGED = 4

    # A previous run created a DataFile record and promised to upload the
    # file (by SCP), but it hasn't been successfully verified by the server,
    # so we should try re-uploading it:
    FOUND_UNVERIFIED_ON_STAGING = 5

    # Missing datafile objects (replicas) on server:
    FOUND_UNVERIFIED_NO_DFOS = 6

    # Lookup failed after retrying, so don't upload in case it has already been uploaded:
    FAILED = 7


class Lookup:
    """
    Model for datafile verification / lookup.
    """

    def __init__(self, folder, datafile_index):
        self.folder_name = folder.name
        self.dataset_id = folder.dataset.id if folder.dataset else None
        self.subdirectory = folder.get_datafile_directory(datafile_index)
        self.datafile_index = datafile_index
        self.filename = folder.get_datafile_name(datafile_index)
        self.message = ""
        self.status = LookupStatus.NOT_STARTED
        self.complete = False

        # If during verification, it has been determined that an
        # unverified DataFile exists on the server for this file,
        # its DataFileModel object will be recorded:
        self.existing_unverified_datafile = None
