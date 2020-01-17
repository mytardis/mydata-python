"""
Test ability to handle dataset-related exceptions.
"""
import os

import requests_mock

from tests.mocks import (
    build_list_response,
    mock_testfacility_user_response,
    EMPTY_LIST_RESPONSE,
    mock_test_facility_response,
    mock_test_instrument_response,
    EXISTING_DATASET_RESPONSE,
)

from tests.fixtures import set_exp_dataset_config


def test_dataset_exceptions(set_exp_dataset_config):
    """Test ability to handle dataset-related exceptions.
    """
    from mydata.conf import settings
    from mydata.models.dataset import Dataset
    from mydata.models.experiment import Experiment
    from mydata.models.folder import Folder
    from mydata.threads.flags import FLAGS

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        owner = settings.general.default_owner
    dataset_folder_name = "Flowers"
    exp_folder_name = "Exp1"
    location = os.path.join(settings.general.data_directory, exp_folder_name)

    # Test creating dataset record and ensure that no exception
    # is raised:
    user_folder_name = owner.username
    group_folder_name = None
    folder = Folder(
        dataset_folder_name, location, user_folder_name, group_folder_name, owner
    )
    folder.experimentTitle = "Existing Experiment"
    mock_exp_response = build_list_response([{"id": 1, "title": "Existing Experiment"}])
    with requests_mock.Mocker() as mocker:
        get_exp_url = (
            "%s/api/v1/mydata_experiment/?format=json&title="
            "&folder_structure=Experiment%%20/%%20Dataset"
            "&user_folder_name=testfacility"
        ) % settings.general.mytardis_url
        mocker.get(get_exp_url, text=mock_exp_response)
        experiment = Experiment.get_exp_for_folder(folder)
    assert experiment.title == "Existing Experiment"
    folder.experiment = experiment
    FLAGS.test_run_running = False

    mock_dataset_response = build_list_response([{"id": 1, "description": "Flowers"}])
    with requests_mock.Mocker() as mocker:
        get_dataset_url = (
            "%s/api/v1/dataset/?format=json&experiments__id=1"
            "&description=Flowers&instrument__id=1"
        ) % settings.general.mytardis_url
        mocker.get(get_dataset_url, text=mock_dataset_response)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)
        dataset = Dataset.create_dataset_if_necessary(folder)
        assert dataset.description == dataset_folder_name

    mock_dataset_response = EMPTY_LIST_RESPONSE
    with requests_mock.Mocker() as mocker:
        get_dataset_url = (
            "%s/api/v1/dataset/?format=json&experiments__id=1"
            "&description=Flowers&instrument__id=1"
        ) % settings.general.mytardis_url
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
        ) % settings.general.mytardis_url
        mocker.get(get_dataset_url, text=EXISTING_DATASET_RESPONSE)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        FLAGS.test_run_running = True
        folder.data_view_fields["name"] = "Existing Dataset"
        dataset = Dataset.create_dataset_if_necessary(folder)
        FLAGS.test_run_running = False
        assert dataset.description == "Existing Dataset"
