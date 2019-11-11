"""
Model class for MyTardis API v1's ReplicaResource.
"""

import requests

from ..settings import SETTINGS


class Replica():
    """
    The Replica model has been removed from MyTardis and replaced by
    the DataFileObject model.  But MyTardis's API still returns
    JSON labeled as "replicas" within each DataFileResource.
    """
    def __init__(self, replica_dict=None):
        self.id = None  # pylint: disable=invalid-name
        self.uri = None
        self.datafile_resource_uri = None
        self.verified = None
        self.__dict__.update(replica_dict)

        if replica_dict is not None:
            for key in replica_dict:
                if hasattr(self, key):
                    self.__dict__[key] = replica_dict[key]
            self.datafile_resource_uri = replica_dict['datafile']

    @staticmethod
    def count_bytes_uploaded_to_staging(dfo_id):
        """
        Count bytes uploaded to staging.

        :raises requests.exceptions.HTTPError:
        """
        url = "%s/api/v1/mydata_replica/%s/?format=json" \
            % (SETTINGS.general.mytardis_url, dfo_id)
        response = requests.get(url=url, headers=SETTINGS.default_headers)
        response.raise_for_status()
        dfo_dict = response.json()
        return dfo_dict['size']

    @property
    def dfo_id(self):
        """
        Returns primary key of the DataFileObject (DFO),
        (also known as a Replica in the MyTardis API).
        """
        return self.id

    @dfo_id.setter
    def dfo_id(self, dfo_id):
        """
        Sets DFO ID, a.k.a. replica ID.

        Only used in tests.
        """
        self.id = dfo_id
