"""
Model class for MyTardis API v1's ReplicaResource.
"""


class Replica:
    """
    The Replica model has been removed from MyTardis and replaced by
    the DataFileObject model.  But MyTardis's API still returns
    JSON labeled as "replicas" within each DataFileResource.
    """

    def __init__(self, replica_dict=None):
        self.id = None  # pylint: disable=invalid-name
        self.uri = None
        self.verified = None
        self.__dict__.update(replica_dict)

        if replica_dict is not None:
            for key in replica_dict:
                if hasattr(self, key):
                    self.__dict__[key] = replica_dict[key]
