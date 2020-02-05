"""
Test ability to handle replica-related exceptions.

'replica' is the name of the MyTardis API resource
endpoint for DataFileObjects (DFOs).
"""
import json

import requests_mock

from tests.fixtures import set_exp_dataset_config


def test_replica_exceptions(set_exp_dataset_config):
    """Test ability to handle replica-related exceptions.

    'replica' is the name of the MyTardis API resource
    endpoint for DataFileObjects (DFOs).
    """
    from mydata.conf import settings
    from mydata.models.datafile import DataFile

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
        assert replica.id == 12345
        assert replica.uri == "dataset1-123/test1.txt"
