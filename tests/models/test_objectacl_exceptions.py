"""
Test ability to handle ObjectACL-related exceptions.
"""
import os

import pytest
import requests_mock

from requests.exceptions import HTTPError

from tests.fixtures import set_exp_dataset_config
from tests.mocks import (
    mock_testfacility_user_response,
    mock_get_group,
    EXISTING_EXP_RESPONSE,
)


def test_objectacl_exceptions(set_exp_dataset_config):
    """Test ability to handle ObjectACL-related exceptions.
    """
    # In a normal MyData run, the settings singleton would only be initialized
    # once, but when running a series of unit tests, we need to ensure that
    # settings is initialized for each test from the MYDATA_CONFIG_PATH
    # environment variable.
    from mydata.conf import settings
    from mydata.models.objectacl import ObjectACL
    from mydata.models.experiment import Experiment
    from mydata.models.folder import Folder
    from mydata.models.group import Group

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        owner = settings.general.default_owner
    dataset_folder_name = "Flowers"
    exp_folder_name = "Exp1"
    location = os.path.join(settings.general.data_directory, exp_folder_name)

    # Test sharing experiment with user, and ensure that no exception
    # is raised:
    user_folder_name = owner.username
    group_folder_name = None
    folder = Folder(
        dataset_folder_name, location, user_folder_name, group_folder_name, owner
    )
    folder.experiment_title = "Existing Experiment"
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Existing%%20Experiment"
            "&folder_structure=Experiment%%20/%%20Dataset&user_folder_name=testfacility"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EXISTING_EXP_RESPONSE)
        experiment = Experiment.get_exp_for_folder(folder)
    assert experiment.title == "Existing Experiment"

    with requests_mock.Mocker() as mocker:
        post_acl_url = "%s/api/v1/objectacl/" % settings.general.mytardis_url
        mocker.post(post_acl_url, status_code=201)
        ObjectACL.share_exp_with_user(experiment, owner)

    # Test sharing experiment with group, and ensure that no exception
    # is raised:
    with requests_mock.Mocker() as mocker:
        mock_get_group(mocker, settings.general.mytardis_url, "TestFacility-Group1")
        group = Group.get_group_by_name("TestFacility-Group1")
        post_acl_url = "%s/api/v1/objectacl/" % settings.general.mytardis_url
        mocker.post(post_acl_url, status_code=201)
        ObjectACL.share_exp_with_group(experiment, group, is_owner=True)

    # Try to create a user ObjectACL record with
    # an invalid API key, which should give 401 (Unauthorized)
    api_key = settings.general.api_key
    settings.general.api_key = "invalid"
    with requests_mock.Mocker() as mocker:
        post_acl_url = "%s/api/v1/objectacl/" % settings.general.mytardis_url
        mocker.post(post_acl_url, status_code=401)
        with pytest.raises(HTTPError) as excinfo:
            ObjectACL.share_exp_with_user(experiment, owner)
        assert excinfo.value.response.status_code == 401
    settings.general.api_key = api_key

    # Try to create a group ObjectACL record with
    # an invalid API key, which should give 401 (Unauthorized)
    api_key = settings.general.api_key
    settings.general.api_key = "invalid"
    with requests_mock.Mocker() as mocker:
        post_acl_url = "%s/api/v1/objectacl/" % settings.general.mytardis_url
        mocker.post(post_acl_url, status_code=401)
        with pytest.raises(HTTPError) as excinfo:
            ObjectACL.share_exp_with_group(experiment, group, is_owner=True)
        assert excinfo.value.response.status_code == 401
    settings.general.api_key = api_key
