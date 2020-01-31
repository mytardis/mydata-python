"""
Models for datafile lookup for indexing
"""


class DataFileCreationStatus:
    """
    Enumerated data type for datafile creation status.
    """

    COMPLETED = 0
    FAILED = 1


class DataFileCreation:
    """
    Model for result of creating a DataFile record on MyTardis.
    """

    def __init__(self, dataset_id, directory, filename, resource_uri, status):
        self.dataset_id = dataset_id
        self.directory = directory
        self.filename = filename
        self.resource_uri = resource_uri
        self.status = DataFileCreationStatus.COMPLETED
