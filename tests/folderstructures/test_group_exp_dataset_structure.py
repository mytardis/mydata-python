"""
Test ability to scan the Group / Experiment / Dataset folder structure.
"""
import requests_mock

from tests.fixtures import set_group_exp_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    mock_get_group,
    mock_test_facility_response,
    mock_test_instrument_response,
)


def test_scan_group_exp_dataset_folders(set_group_exp_dataset_config):
    """Test ability to scan the Group / Experiment / Dataset folder structure.
    """
    from mydata.conf import settings
    from mydata.tasks.folders import scan_folders

    groups = []
    exps = []
    folders = []

    # We don't need callback for finding users folders:
    found_user = None

    def found_group(group):
        groups.append(group)

    def found_exp(exp_folder_name):
        exps.append(exp_folder_name)

    def found_dataset(folder):
        folders.append(folder)

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        for group_name in ("TestFacility-Group1", "TestFacility-Group2"):
            mock_get_group(mocker, settings.general.mytardis_url, group_name)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        scan_folders(found_user, found_group, found_exp, found_dataset)

    assert sorted([group.name for group in groups]) == [
        "TestFacility-Group1",
        "TestFacility-Group2",
    ]
    assert sorted(exps) == ["Exp1", "Exp2"]
    assert sorted([folder.name for folder in folders]) == ["Birds", "Flowers"]
    assert sum([folder.num_files for folder in folders]) == 5
