"""
Test ability to handle replica-related exceptions.

'replica' is the name of the MyTardis API resource
endpoint for DataFileObjects (DFOs).
"""
import json
import pytest

import requests_mock
from requests.exceptions import HTTPError

from tests.fixtures import set_exp_dataset_config


def test_replica_exceptions(set_exp_dataset_config):
    """Test ability to handle replica-related exceptions.

    'replica' is the name of the MyTardis API resource
    endpoint for DataFileObjects (DFOs).
    """
    from mydata.conf import settings
    from mydata.models.datafile import DataFile
    from mydata.models.replica import Replica

    mock_datafile_response = json.dumps(
        {
            "id": 1,
            "filename": "test1.txt",
            "replicas": [
                {
                    "id": 12345,
                    "datafile": "/api/v1/dataset_file/1234/",
                    "location": "local-storage",
                    "resource_uri": "/api/v1/replica/12345/",
                    "uri": "dataset1-123/test1.txt",
                    "verified": True,
                }
            ],
        }
    )
    with requests_mock.Mocker() as mocker:
        get_datafile_url = (
            "%s/api/v1/mydata_dataset_file/12345/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_datafile_url, text=mock_datafile_response)
        datafile = DataFile.get_datafile_from_id(12345)
        replica = datafile.replicas[0]

    mock_replica_response = json.dumps(
        {
            "id": 12345,
            "datafile": "/api/v1/dataset_file/1234/",
            "location": "local-storage",
            "resource_uri": "/api/v1/mydata_replica/12345/",
            "size": 1024,
            "uri": "dataset1-123/test1.txt",
            "verified": True,
        }
    )
    with requests_mock.Mocker() as mocker:
        get_replica_url = (
            "%s/api/v1/mydata_replica/12345/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_replica_url, text=mock_replica_response)
        bytes_on_staging = Replica.count_bytes_uploaded_to_staging(replica.dfo_id)
        assert bytes_on_staging == 1024

    api_key = settings.general.api_key
    settings.general.api_key = "invalid"
    with requests_mock.Mocker() as mocker:
        get_replica_url = (
            "%s/api/v1/mydata_replica/12345/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_replica_url, status_code=401)
        with pytest.raises(HTTPError) as excinfo:
            _ = Replica.count_bytes_uploaded_to_staging(replica.dfo_id)
        assert excinfo.value.response.status_code == 401
        settings.general.api_key = api_key

    with requests_mock.Mocker() as mocker:
        get_replica_url = (
            "%s/api/v1/mydata_replica/12345/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_replica_url, status_code=404)
        with pytest.raises(HTTPError) as excinfo:
            _ = Replica.count_bytes_uploaded_to_staging(replica.dfo_id)
        assert excinfo.value.response.status_code == 404
