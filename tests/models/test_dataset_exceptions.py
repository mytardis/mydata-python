"""
Test ability to handle dataset-related exceptions.
"""
import importlib
import json
import os

import pytest
import requests_mock
from requests.exceptions import HTTPError

from mydata.threads.flags import FLAGS

@pytest.fixture
def set_mydata_config_path():
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-exp-dataset.cfg'))


def test_dataset_exceptions(set_mydata_config_path):
    """Test ability to handle dataset-related exceptions.
    """
    from mydata import settings
    settings = importlib.reload(settings)
    from mydata.models import facility
    facility = importlib.reload(facility)
    from mydata.models import folder
    folder = importlib.reload(folder)
    SETTINGS = settings.SETTINGS
    assert SETTINGS.config_path == os.environ['MYDATA_CONFIG_PATH']
    from mydata.models.dataset import Dataset
    from mydata.models.experiment import Experiment
    from mydata.models.folder import Folder
    from mydata.models.settings.validation import validate_settings

    mock_api_endpoints = {
        "dataset": {
            "list_endpoint": "/api/v1/dataset/",
            "schema": "/api/v1/dataset/schema/"
        },
        "experiment": {
            "list_endpoint": "/api/v1/experiment/",
            "schema": "/api/v1/experiment/schema/"
        }
    }
    mock_api_response = json.dumps(mock_api_endpoints)
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
    mock_facility_dict = {
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 1
        },
        "objects": [{
            "id": 1,
            "name": "Test Facility",
            "manager_group": {
                "id": 1,
                "name": "test-facility-managers"
            }
        }]
    }
    mock_facility_response = json.dumps(mock_facility_dict)
    mock_instrument_dict = {
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 1
        },
        "objects": [{
            "id": 1,
            "name": "Test Instrument",
            "facility": {
                "id": 1,
                "name": "Test Facility",
                "manager_group": {
                    "id": 1,
                    "name": "test-facility-managers"
                }
            }
        }]
    }
    mock_instrument_response = json.dumps(mock_instrument_dict)
    with requests_mock.Mocker() as mocker:
        list_api_endpoints_url = "%s/api/v1/?format=json" % SETTINGS.general.mytardis_url
        mocker.get(list_api_endpoints_url, text=mock_api_response)
        get_user_api_url = "%s/api/v1/user/?format=json&username=testfacility" % SETTINGS.general.mytardis_url
        mocker.get(get_user_api_url, text=mock_user_response)
        get_facility_api_url = "%s/api/v1/facility/?format=json" % SETTINGS.general.mytardis_url
        mocker.get(get_facility_api_url, text=mock_facility_response)
        get_instrument_api_url = "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument" % SETTINGS.general.mytardis_url
        mocker.get(get_instrument_api_url, text=mock_instrument_response)
        validate_settings()

    with requests_mock.Mocker() as mocker:
        get_user_api_url = "%s/api/v1/user/?format=json&username=testfacility" % SETTINGS.general.mytardis_url
        mocker.get(get_user_api_url, text=mock_user_response)
        owner = SETTINGS.general.default_owner
    dataset_folder_name = "Flowers"
    exp_folder_name = "Exp1"
    location = os.path.join(SETTINGS.general.data_directory, exp_folder_name)

    # Test creating dataset record and ensure that no exception
    # is raised:
    user_folder_name = owner.username
    group_folder_name = None
    folder = Folder(dataset_folder_name, location,
                    user_folder_name, group_folder_name, owner)
    folder.experimentTitle = "Existing Experiment"
    mock_exp_dict = {
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 1
        },
        "objects": [{
            "id": 1,
            "title": "Existing Experiment"
        }]
    }
    mock_exp_response = json.dumps(mock_exp_dict)
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title="
            "&folder_structure=Experiment%%20/%%20Dataset"
            "&user_folder_name=testfacility"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_exp_url, text=mock_exp_response)
        experiment = Experiment.get_exp_for_folder(folder)
    assert experiment.title == "Existing Experiment"
    folder.experiment = experiment
    FLAGS.test_run_running = False

    mock_dataset_dict = {
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 1
        },
        "objects": [{
            "id": 1,
            "description": "Flowers"
        }]
    }
    mock_dataset_response = json.dumps(mock_dataset_dict)
    with requests_mock.Mocker() as mocker:
        get_dataset_url = (
            "%s/api/v1/dataset/?format=json&experiments__id=1"
            "&description=Flowers&instrument__id=1"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_dataset_url, text=mock_dataset_response)
        dataset = Dataset.create_dataset_if_necessary(folder)
        assert dataset.description == dataset_folder_name

    mock_dataset_dict = {
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 0
        },
        "objects": [
        ]
    }
    mock_dataset_response = json.dumps(mock_dataset_dict)
    with requests_mock.Mocker() as mocker:
        get_dataset_url = (
            "%s/api/v1/dataset/?format=json&experiments__id=1"
            "&description=Flowers&instrument__id=1"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_dataset_url, text=mock_dataset_response)
        # Simulate creating dataset record during test run
        # and ensure that no exception is raised:
        FLAGS.test_run_running = True
        dataset = Dataset.create_dataset_if_necessary(folder)
        assert dataset == None
        FLAGS.test_run_running = False

    mock_dataset_dict = {
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 1
        },
        "objects": [{
            "id": 1,
            "description": "Existing Dataset"
        }]
    }
    mock_dataset_response = json.dumps(mock_dataset_dict)
    with requests_mock.Mocker() as mocker:
        get_dataset_url = (
            "%s/api/v1/dataset/?format=json&experiments__id=1"
            "&description=Existing%%20Dataset&instrument__id=1"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_dataset_url, text=mock_dataset_response)
        # Simulate retrieving existing dataset record during test run
        # and ensure that no exception is raised:
        FLAGS.test_run_running = True
        folder.data_view_fields['folder_name'] = "Existing Dataset"
        dataset = Dataset.create_dataset_if_necessary(folder)
        FLAGS.test_run_running = False
        assert dataset.description == "Existing Dataset"
