"""
Test ability to scan the Experiment / Dataset folder structure.
"""
import requests_mock

from tests.fixtures import set_exp_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    mock_test_facility_response,
    mock_test_instrument_response,
)


def test_scan_exp_dataset_folders(set_exp_dataset_config):
    """Test ability to scan the Experiment / Dataset folder structure.
    """
    from mydata.conf import settings
    from mydata.tasks.folders import scan_folders

    exps = []
    folders = []

    # We don't need callbacks for these in this case:
    found_user = None
    found_group = None

    def found_exp(exp_folder_name):
        exps.append(exp_folder_name)

    def found_dataset(folder):
        folders.append(folder)

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        scan_folders(found_user, found_group, found_exp, found_dataset)

    assert sorted(exps) == ["Exp1", "Exp2"]
    assert sorted([folder.name for folder in folders]) == ["Birds", "Flowers"]
    assert sum([folder.num_files for folder in folders]) == 5
