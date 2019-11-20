"""
Test ability to handle experiment-related exceptions.
"""
import json
import os

import pytest
import requests_mock
from requests.exceptions import HTTPError

from tests.mocks import (
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE,
    EXISTING_EXP_RESPONSE,
    EXP1_RESPONSE,
    EMPTY_LIST_RESPONSE
)

from tests.fixtures import set_exp_dataset_config


def test_experiment_exceptions(set_exp_dataset_config):
    """Test ability to handle experiment-related exceptions.
    """
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    from mydata.conf import settings
    from mydata.threads.flags import FLAGS
    from mydata.models.experiment import Experiment
    from mydata.models.folder import Folder

    # MyData has the concept of a "default experiment",
    # which depends on the UUID of the MyData instance:
    settings.miscellaneous.uuid = "1234567890"

    mock_user_dict = {
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 1
        },
        "objects": [{
            "id": 1,
            "username": "testfacility",
            "first_name": "TestFacility",
            "last_name": "RoleAccount",
            "email": "testfacility@example.com",
            "groups": [{
                "id": 1,
                "name": "test-facility-managers"
            }]
        }]
    }
    mock_user_response = json.dumps(mock_user_dict)
    with requests_mock.Mocker() as mocker:
        get_user_api_url = "%s/api/v1/user/?format=json&username=testfacility" % settings.general.mytardis_url
        mocker.get(get_user_api_url, text=mock_user_response)
        owner = settings.general.default_owner
    dataset_folder_name = "Flowers"
    exp_folder_name = "Exp1"
    location = os.path.join(settings.general.data_directory, exp_folder_name)

    # LOOKING UP EXPERIMENTS

    # Try to look up nonexistent experiment record with
    # experiment title set manually, and with a user folder
    # name, but no group folder name:
    user_folder_name = owner.username
    group_folder_name = None
    folder = Folder(
        dataset_folder_name, location, user_folder_name, group_folder_name, owner)
    folder.experiment_title = exp_folder_name

    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Exp1"
            "&folder_structure=Experiment%%20/%%20Dataset"
            "&user_folder_name=testfacility"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EMPTY_LIST_RESPONSE)

        existing_exp = Experiment.get_exp_for_folder(folder)
        assert not existing_exp

    # Look up existing experiment record with
    # experiment title set manually, and with a user folder
    # name, but no group folder name:
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json"
            "&title=Existing%%20Experiment"
            "&folder_structure=Experiment%%20/%%20Dataset"
            "&user_folder_name=testfacility"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EXISTING_EXP_RESPONSE)
        user_folder_name = owner.username
        group_folder_name = None
        folder = Folder(
            dataset_folder_name, location, user_folder_name, group_folder_name, owner)
        folder.experiment_title = "Existing Experiment"
        experiment = Experiment.get_exp_for_folder(folder)
        assert experiment.title == "Existing Experiment"

    # Look up one of many existing experiment records with
    # experiment title set manually, and with a user folder
    # name, but no group folder name:
    mock_exp_dict = {
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 2
        },
        "objects": [
            {
                "id": 1,
                "title": "Existing Experiment1"
            },
            {
                "id": 2,
                "title": "Existing Experiment2"
            }
        ]
    }
    mock_exp_response = json.dumps(mock_exp_dict)
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json"
            "&title=Multiple%%20Existing%%20Experiments"
            "&folder_structure=Experiment%%20/%%20Dataset"
            "&user_folder_name=testfacility"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=mock_exp_response)
        user_folder_name = owner.username
        group_folder_name = None
        folder = Folder(
            dataset_folder_name, location, user_folder_name, group_folder_name, owner)
        folder.experiment_title = "Multiple Existing Experiments"
        experiment = Experiment.get_exp_for_folder(folder)
        assert experiment.title == "Existing Experiment1"

    # Try to look up nonexistent experiment record with
    # experiment title set manually, and with a group folder
    # name, but no user folder name:
    user_folder_name = None
    group_folder_name = "Test Group1"
    folder = Folder(
        dataset_folder_name, location, user_folder_name, group_folder_name, owner)
    folder.experiment_title = exp_folder_name
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Exp1"
            "&folder_structure=Experiment%%20/%%20Dataset"
            "&group_folder_name=Test%%20Group1"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EMPTY_LIST_RESPONSE)
        existing_exp = Experiment.get_exp_for_folder(folder)
        assert not existing_exp

    # Look up existing experiment record with
    # experiment title set manually, and with a group folder
    # name, but no user folder name:
    user_folder_name = None
    group_folder_name = "Test Group1"
    folder = Folder(
        dataset_folder_name, location, user_folder_name, group_folder_name, owner)
    folder.experiment_title = "Existing Experiment"
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Existing%%20Experiment"
            "&folder_structure=Experiment%%20/%%20Dataset&group_folder_name=Test%%20Group1"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EXISTING_EXP_RESPONSE)
        experiment = Experiment.get_exp_for_folder(folder)
        assert experiment.title == "Existing Experiment"

    # Try to look up nonexistent experiment record with
    # experiment title set manually, and with a user folder
    # name, and a group folder name:
    user_folder_name = owner.username
    group_folder_name = "Test Group1"
    folder = Folder(
        dataset_folder_name, location, user_folder_name, group_folder_name, owner)
    folder.experiment_title = exp_folder_name
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Exp1"
            "&folder_structure=Experiment%%20/%%20Dataset"
            "&group_folder_name=Test%%20Group1"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EMPTY_LIST_RESPONSE)
        existing_exp = Experiment.get_exp_for_folder(folder)
        assert not existing_exp

    # Look up existing experiment record with
    # experiment title set manually, and with a group folder
    # name, and a user folder name:
    user_folder_name = owner.username
    group_folder_name = "Test Group1"
    folder = Folder(
        dataset_folder_name, location, user_folder_name, group_folder_name, owner)
    folder.experiment_title = "Existing Experiment"
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Existing%%20Experiment"
            "&folder_structure=Experiment%%20/%%20Dataset"
            "&user_folder_name=testfacility&group_folder_name=Test%%20Group1"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EXISTING_EXP_RESPONSE)
        experiment = Experiment.get_exp_for_folder(folder)
        assert experiment.title == "Existing Experiment"

    # Try to look up nonexistent experiment record with
    # experiment title set manually, with neither a user folder
    # name, nor a group folder name:
    user_folder_name = None
    group_folder_name = None
    folder = Folder(
        dataset_folder_name, location, user_folder_name, group_folder_name, owner)
    folder.experiment_title = exp_folder_name
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Exp1"
            "&folder_structure=Experiment%%20/%%20Dataset"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EMPTY_LIST_RESPONSE)
        existing_exp = Experiment.get_exp_for_folder(folder)
        assert not existing_exp

    # Look up existing experiment record with
    # experiment title set manually, and with neither a user folder
    # name, nor a group folder name:
    user_folder_name = None
    group_folder_name = None
    folder = Folder(
        dataset_folder_name, location, user_folder_name, group_folder_name, owner)
    folder.experiment_title = "Existing Experiment"
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Existing%%20Experiment"
            "&folder_structure=Experiment%%20/%%20Dataset"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EXISTING_EXP_RESPONSE)
        experiment = Experiment.get_exp_for_folder(folder)
        assert experiment.title == "Existing Experiment"

    # Try to look up experiment record with
    # an invalid API key, which should give 401 (Unauthorized)
    api_key = settings.general.api_key
    settings.general.api_key = "invalid"
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Existing%%20Experiment"
            "&folder_structure=Experiment%%20/%%20Dataset"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, status_code=401)
        with pytest.raises(HTTPError) as excinfo:
            _ = Experiment.get_exp_for_folder(folder)
        assert excinfo.value.response.status_code == 401
        settings.general.api_key = api_key

    # Try to look up experiment record with a missing Schema,
    # which can result in a 404 from the MyTardis API:
    folder.experiment_title = "Missing Schema"
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Missing%%20Schema"
            "&folder_structure=Experiment%%20/%%20Dataset"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, status_code=404)
        with pytest.raises(HTTPError) as excinfo:
            _ = Experiment.get_exp_for_folder(folder)
        assert excinfo.value.response.status_code == 404

    # Try to look up experiment record and handle a 404 of
    # unknown origin from the MyTardis API:
    folder.experiment_title = "Unknown 404"
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Unknown%%20404"
            "&folder_structure=Experiment%%20/%%20Dataset"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, status_code=404)
        with pytest.raises(HTTPError) as excinfo:
            _ = Experiment.get_exp_for_folder(folder)
        assert excinfo.value.response.status_code == 404

    # CREATING EXPERIMENTS

    # Try to create an experiment with a title specified manually
    # and check that the title is correct:
    FLAGS.test_run_running = False
    folder.experiment_title = exp_folder_name
    with requests_mock.Mocker() as mocker:
        post_exp_url = "%s/api/v1/mydata_experiment/" % settings.general.mytardis_url
        mocker.post(post_exp_url, text=EXP1_RESPONSE, status_code=201)
        post_objectacl_url = "%s/api/v1/objectacl/" % settings.general.mytardis_url
        mocker.post(post_objectacl_url, status_code=201)
        get_facility_api_url = "%s/api/v1/facility/?format=json" % settings.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument" % settings.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)
        experiment = Experiment.create_exp_for_folder(folder)
        assert experiment.title == exp_folder_name

    # Try to create an experiment with a title specified manually,
    # during a test run
    FLAGS.test_run_running = True
    folder.experiment_title = exp_folder_name
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title=Exp1"
            "&folder_structure=Experiment%%20/%%20Dataset"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EMPTY_LIST_RESPONSE)
        experiment = Experiment.get_or_create_exp_for_folder(folder)
        assert experiment is None
        FLAGS.test_run_running = False

    # Get or create an experiment with a title specified manually,
    # which already exists during a test run
    FLAGS.test_run_running = True
    folder.experiment_title = "Existing Experiment"
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json"
            "&title=Existing%%20Experiment&folder_structure=Experiment%%20/%%20Dataset"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=EXISTING_EXP_RESPONSE)
        experiment = Experiment.get_or_create_exp_for_folder(folder)
        assert experiment.title == "Existing Experiment"
        folder.experiment_title = exp_folder_name
        FLAGS.test_run_running = False

    # Try to create an experiment record with
    # an invalid API key, which should give 401 (Unauthorized)
    api_key = settings.general.api_key
    settings.general.api_key = "invalid"
    with requests_mock.Mocker() as mocker:
        post_exp_url = (
            "%s/api/v1/mydata_experiment/"
        ) % settings.general.mytardis_url
        mocker.post(post_exp_url, status_code=401)
        get_facility_api_url = "%s/api/v1/facility/?format=json" % settings.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument" % settings.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)
        with pytest.raises(HTTPError) as excinfo:
            _ = Experiment.create_exp_for_folder(folder)
        assert excinfo.value.response.status_code == 401
        settings.general.api_key = api_key

    # Now let's test experiment creation with the experiment's
    # title determined automatically (from the instrument's name
    # which becomes the default uploader name) and the user folder
    # name or group folder name):
    user_folder_name = owner.username
    group_folder_name = None
    folder = Folder(
        dataset_folder_name, location, user_folder_name, group_folder_name, owner)

    # Test case where MyTardis API returns a 404, e.g. because a
    # requested Experiment Schema can't be found.
    folder.experiment_title = "Request 404 from Fake MyTardis Server"
    with requests_mock.Mocker() as mocker:
        post_exp_url = (
            "%s/api/v1/mydata_experiment/"
        ) % settings.general.mytardis_url
        mocker.post(post_exp_url, status_code=404)
        get_facility_api_url = "%s/api/v1/facility/?format=json" % settings.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument" % settings.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)
        with pytest.raises(HTTPError) as excinfo:
            _ = Experiment.create_exp_for_folder(folder)
        assert excinfo.value.response.status_code == 404
