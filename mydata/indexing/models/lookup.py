"""
Models for datafile lookup for indexing
"""


class LookupStatus:
    """
    Enumerated data type for lookup states.
    """

    # Not found on MyTardis, need to create a DataFile record for this file:
    NOT_FOUND = 0

    # Found on MyTardis (and verified), no need to create a DataFile record for this file:
    FOUND_VERIFIED = 1

    # Found matching DataFile record with an unverified DataFileObject (replica):
    FOUND_UNVERIFIED = 2

    # Missing DataFileObjects (replicas) on server:
    FOUND_UNVERIFIED_NO_DFOS = 3

    # Lookup failed - should continue to the next file, unless the failure
    # was so serious (e.g. no network) that we need to abort everything:
    FAILED = 4


class Lookup:
    """
    Model for result of looking for a matching DataFile record on MyTardis
    to see if a file needs indexing.
    """

    def __init__(self, dataset_id, directory, filename, status):
        self.dataset_id = dataset_id
        self.directory = directory
        self.filename = filename
        self.status = status
