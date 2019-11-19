"""
Test ability to handle group-related exceptions.
"""
import json

import pytest
import requests_mock

from requests.exceptions import HTTPError

from tests.mocks import MOCK_GROUP_RESPONSE
from tests.fixtures import set_exp_dataset_config


def test_group_exceptions(set_exp_dataset_config):
    """Test ability to handle group-related exceptions.
    """
    from mydata.settings import SETTINGS
    from mydata.models.group import Group

    # Test retrieving a valid group record (using the Group model's
    # get_group_by_name method) and ensure that no exception is raised:
    with requests_mock.Mocker() as mocker:
        get_group_url = (
            "%s/api/v1/group/?format=json&name=TestFacility-Group1"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_group_url, text=MOCK_GROUP_RESPONSE)
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
        group = Group.get_group_by_name("INVALID_GROUP")
        assert not group
