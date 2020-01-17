"""
Test ability to scan the Dataset folder structure.
"""
import requests_mock

from tests.fixtures import set_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    mock_test_facility_response,
    mock_test_instrument_response,
)


def test_scan_dataset_folders(set_dataset_config):
    """Test ability to scan the Dataset folder structure.
    """
    from mydata.conf import settings
    from mydata.tasks.folders import scan_folders

    folders = []

    # We don't need callbacks for these in this case:
    found_exp = None
    found_user = None
    found_group = None

    def found_dataset(folder):
        folders.append(folder)

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        scan_folders(found_user, found_group, found_exp, found_dataset)

    assert sorted([folder.name for folder in folders]) == ["Birds", "Flowers"]
    assert sum([folder.num_files for folder in folders]) == 5
