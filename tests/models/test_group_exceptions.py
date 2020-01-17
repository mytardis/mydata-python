"""
Test ability to handle group-related exceptions.
"""
import pytest
import requests_mock

from requests.exceptions import HTTPError

from tests.mocks import EMPTY_LIST_RESPONSE, MOCK_GROUP_RESPONSE
from tests.fixtures import set_exp_dataset_config


def test_group_exceptions(set_exp_dataset_config):
    """Test ability to handle group-related exceptions.
    """
    from mydata.conf import settings
    from mydata.models.group import Group

    # Test retrieving a valid group record (using the Group model's
    # get_group_by_name method) and ensure that no exception is raised:
    with requests_mock.Mocker() as mocker:
        get_group_url = (
            "%s/api/v1/group/?format=json&name=TestFacility-Group1"
        ) % settings.general.mytardis_url
        mocker.get(get_group_url, text=MOCK_GROUP_RESPONSE)
        group = Group.get_group_by_name("TestFacility-Group1")
        assert group.name == "TestFacility-Group1"
        assert group.get_value_for_key("name") == group.name

    # Try to look up group record with an invalid API key,
    # which should give 401 (Unauthorized).
    api_key = settings.general.api_key
    settings.general.api_key = "invalid"
    with requests_mock.Mocker() as mocker:
        get_group_url = (
            "%s/api/v1/group/?format=json&name=TestFacility-Group1"
        ) % settings.general.mytardis_url
        mocker.get(get_group_url, status_code=401)
        with pytest.raises(HTTPError) as excinfo:
            _ = Group.get_group_by_name("TestFacility-Group1")
        assert excinfo.value.response.status_code == 401
    settings.general.api_key = api_key

    with requests_mock.Mocker() as mocker:
        get_group_url = (
            "%s/api/v1/group/?format=json&name=INVALID_GROUP"
        ) % settings.general.mytardis_url
        mocker.get(get_group_url, text=EMPTY_LIST_RESPONSE)
        group = Group.get_group_by_name("INVALID_GROUP")
        assert not group
