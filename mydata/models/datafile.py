"""
Model class for MyTardis API v1's DataFileResource.
"""

import io
import json
import urllib.parse

import requests
from requests_toolbelt.multipart import encoder

from ..conf import settings
from ..logs import logger
from ..utils.exceptions import MultipleObjectsReturned
from .replica import Replica


class DataFile():
    """
    Model class for MyTardis API v1's DataFileResource.
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, dataset, datafile_dict):
        self.id = None  # pylint: disable=invalid-name
        self.filename = None
        self.directory = None
        self.size = None
        self.replicas = []
        if datafile_dict is not None:
            for key in datafile_dict:
                if hasattr(self, key):
                    self.__dict__[key] = datafile_dict[key]
            self.replicas = []
            for replica_dict in datafile_dict['replicas']:
                self.replicas.append(Replica(replica_dict=replica_dict))
        # This needs to go after self.__dict__[key] = datafile_dict[key]
        # so we get the full dataset model, not just the API resource string:
        self.dataset = dataset

    @staticmethod
    def get_datafile(dataset, filename, directory):
        """
        Lookup datafile by dataset, filename and directory.

        Return DataFile instance if found.
        Return None if not found.
        Raise MultipleObjectsReturned if multiple matches found.

        :raises requests.exceptions.HTTPError:
        """
        mytardis_url = settings.general.mytardis_url
        url = mytardis_url + "/api/v1/mydata_dataset_file/?format=json" + \
            "&dataset__id=" + str(dataset.dataset_id) + \
            "&filename=" + urllib.parse.quote(filename.encode('utf-8')) + \
            "&directory=" + urllib.parse.quote(directory.encode('utf-8'))
        response = requests.get(url=url, headers=settings.default_headers)
        response.raise_for_status()
        datafiles_dict = response.json()
        num_datafiles_found = datafiles_dict['meta']['total_count']
        if num_datafiles_found == 0:
            return None
        if num_datafiles_found > 1:
            raise MultipleObjectsReturned(
                message="Multiple datafiles matching %s were found in MyTardis"
                % filename,
                response=response)
        return DataFile(
            dataset=dataset, datafile_dict=datafiles_dict['objects'][0])

    @staticmethod
    def get_datafile_from_id(datafile_id):
        """
        Lookup datafile by ID.

        :raises requests.exceptions.HTTPError:
        """
        mytardis_url = settings.general.mytardis_url
        url = "%s/api/v1/mydata_dataset_file/%s/?format=json" \
            % (mytardis_url, datafile_id)
        response = requests.get(url=url, headers=settings.default_headers)
        response.raise_for_status()
        datafile_dict = response.json()
        return DataFile(dataset=None, datafile_dict=datafile_dict)

    @staticmethod
    def verify(datafile_id):
        """
        Verify a datafile via the MyTardis API.
        """
        mytardis_url = settings.general.mytardis_url
        url = mytardis_url + "/api/v1/dataset_file/%s/verify/" % datafile_id
        response = requests.get(url=url, headers=settings.default_headers)
        if response.status_code < 200 or response.status_code >= 300:
            logger.warning("Failed to verify datafile id \"%s\" " % datafile_id)
            logger.warning(response.text)
        # Returning True doesn't mean that the file has been verified.
        # It just means that the MyTardis API has accepted our verification
        # request without raising an error.  The verification is asynchronous
        # so it might not happen immediately if there is congestion in the
        # Celery queue.
        return True

    @staticmethod
    def create_datafile_for_staging_upload(datafile_dict):
        """
        Create a DataFile record and return a temporary URL to upload
        to (e.g. by SCP).
        """
        url = "%s/api/v1/mydata_dataset_file/" % settings.general.mytardis_url
        datafile_json = json.dumps(datafile_dict)
        response = requests.post(headers=settings.default_headers,
                                 url=url, data=datafile_json.encode())
        return response

    @staticmethod
    def upload_datafile_with_post(
            datafile_path, datafile_dict, upload, progress_callback):
        """
        Upload a file to the MyTardis API via POST, creating a new
        DataFile record.
        """
        # from ..dataviewmodels.dataview import DATAVIEW_MODELS
        url = "%s/api/v1/mydata_dataset_file/" % settings.general.mytardis_url
        # message = "Initializing buffered reader..."
        # DATAVIEW_MODELS['uploads'].SetMessage(upload, message)
        upload.buffered_reader = io.open(datafile_path, 'rb')

        encoded = encoder.MultipartEncoder(
            fields={"json_data": json.dumps(datafile_dict),
                    'attached_file': (upload.filename,
                                      upload.buffered_reader,
                                      'application/octet-stream')})
        # Workaround for issue with httplib's hard-coded read size
        # of 8192 bytes which can lead to slow uploads, see:
        # http://toolbelt.readthedocs.io/en/latest/uploading-data.html
        # https://github.com/requests/toolbelt/issues/75
        multipart_encoder_read_method = encoded.read
        encoded.read = lambda size: multipart_encoder_read_method(1024*1024)

        multipart = encoder.MultipartEncoderMonitor(encoded, progress_callback)

        headers = settings.default_headers
        headers['Content-Type'] = multipart.content_type
        response = requests.post(url, data=multipart, headers=headers)
        return response
