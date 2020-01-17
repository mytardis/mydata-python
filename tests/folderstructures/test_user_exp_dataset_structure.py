"""
Test ability to scan the Username / Experiment / Dataset folder structure.
"""
import requests_mock

from tests.fixtures import set_user_exp_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    mock_testuser_response,
    mock_test_facility_response,
    mock_test_instrument_response,
)


def test_scan_user_exp_dataset_folders(set_user_exp_dataset_config):
    """Test ability to scan the Username / Experiment / Dataset folder structure.
    """
    from mydata.conf import settings
    from mydata.tasks.folders import scan_folders

    users = []
    exps = []
    folders = []

    def found_user(user):
        users.append(user)

    def found_exp(exp_folder_name):
        exps.append(exp_folder_name)

    found_group = None

    def found_dataset(folder):
        folders.append(folder)

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        for username in ("testuser1", "testuser2"):
            mock_testuser_response(
                mocker,
                settings.general.mytardis_url,
                settings.advanced.folder_structure,
                username,
            )
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        scan_folders(found_user, found_group, found_exp, found_dataset)

    assert sorted([user.username for user in users]) == ["testuser1", "testuser2"]
    assert sorted(exps) == ["Exp1", "Exp2"]
    assert sorted([folder.name for folder in folders]) == ["Birds", "Flowers"]
    assert sum([folder.num_files for folder in folders]) == 5
