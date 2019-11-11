"""
Test ability to handle group-related exceptions.
"""
import importlib
import json
import os

import pytest
import requests_mock

from requests.exceptions import HTTPError


@pytest.fixture
def set_mydata_config_path():
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-exp-dataset.cfg'))


def test_group_exceptions(set_mydata_config_path):
    """Test ability to handle group-related exceptions.
    """
    from mydata import settings
    from mydata.models.group import Group
    from mydata.utils.exceptions import DoesNotExist
    settings = importlib.reload(settings)
    SETTINGS = settings.SETTINGS  # pylint: disable=invalid-name

    # Test retrieving a valid group record (using the Group model's
    # get_group_by_name method) and ensure that no exception is raised:
    mock_group_response = json.dumps({
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 1
        },
        "objects": [{
            "id": 1,
            "name": "TestFacility-Group1",
        }]
    })
    with requests_mock.Mocker() as mocker:
        get_group_url = (
            "%s/api/v1/group/?format=json&name=TestFacility-Group1"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_group_url, text=mock_group_response)
        group = Group.get_group_by_name("TestFacility-Group1")
        assert group.name == "TestFacility-Group1"
        assert group.get_value_for_key('name') == group.name

    # Try to look up group record with an invalid API key,
    # which should give 401 (Unauthorized).
    api_key = SETTINGS.general.api_key
    SETTINGS.general.api_key = "invalid"
    with requests_mock.Mocker() as mocker:
        get_group_url = (
            "%s/api/v1/group/?format=json&name=TestFacility-Group1"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_group_url, status_code=401)
        with pytest.raises(HTTPError) as excinfo:
            _ = Group.get_group_by_name("TestFacility-Group1")
        assert excinfo.value.response.status_code == 401
    SETTINGS.general.api_key = api_key

    empty_group_response = json.dumps({
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 0
        },
        "objects": []
    })
    with requests_mock.Mocker() as mocker:
        get_group_url = (
            "%s/api/v1/group/?format=json&name=INVALID_GROUP"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_group_url, text=empty_group_response)
        with pytest.raises(DoesNotExist):
            _ = Group.get_group_by_name("INVALID_GROUP")
