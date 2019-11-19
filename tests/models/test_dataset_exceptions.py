"""
Test ability to handle dataset-related exceptions.
"""
import json
import os

import requests_mock

from tests.mocks import (
    MOCK_USER_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE,
    EXISTING_DATASET_RESPONSE
)

from tests.fixtures import set_exp_dataset_config


def test_dataset_exceptions(set_exp_dataset_config):
    """Test ability to handle dataset-related exceptions.
    """
    from mydata.settings import SETTINGS
    from mydata.models.dataset import Dataset
    from mydata.models.experiment import Experiment
    from mydata.models.folder import Folder
    from mydata.threads.flags import FLAGS

    with requests_mock.Mocker() as mocker:
        get_user_api_url = "%s/api/v1/user/?format=json&username=testfacility" % SETTINGS.general.mytardis_url
        mocker.get(get_user_api_url, text=MOCK_USER_RESPONSE)
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
    mock_exp_response = json.dumps({
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
    })
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

    mock_dataset_response = json.dumps({
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
    })
    with requests_mock.Mocker() as mocker:
        get_dataset_url = (
            "%s/api/v1/dataset/?format=json&experiments__id=1"
            "&description=Flowers&instrument__id=1"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_dataset_url, text=mock_dataset_response)
        get_facility_api_url = "%s/api/v1/facility/?format=json" % SETTINGS.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)
        dataset = Dataset.create_dataset_if_necessary(folder)
        assert dataset.description == dataset_folder_name

    mock_dataset_response = json.dumps({
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 0
        },
        "objects": [
        ]
    })
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
        assert dataset is None
        FLAGS.test_run_running = False

    # Simulate retrieving existing dataset record during test run
    # and ensure that no exception is raised:
    with requests_mock.Mocker() as mocker:
        get_dataset_url = (
            "%s/api/v1/dataset/?format=json&experiments__id=1"
            "&description=Existing%%20Dataset&instrument__id=1"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_dataset_url, text=EXISTING_DATASET_RESPONSE)
        get_facility_api_url = "%s/api/v1/facility/?format=json" % SETTINGS.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        FLAGS.test_run_running = True
        folder.data_view_fields['name'] = "Existing Dataset"
        dataset = Dataset.create_dataset_if_necessary(folder)
        FLAGS.test_run_running = False
        assert dataset.description == "Existing Dataset"
