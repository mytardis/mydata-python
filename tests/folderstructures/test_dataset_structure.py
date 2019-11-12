"""
Test ability to scan the Dataset folder structure.
"""
import requests_mock

from tests.fixtures import set_dataset_config

from tests.mocks import (
    MOCK_USER_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE
)

def test_scan_dataset_folders(set_dataset_config):
    """Test ability to scan the Dataset folder structure.
    """
    from mydata.settings import SETTINGS
    from mydata.tasks import scan_folders

    folders = []

    def found_user_or_group(num_user_or_group_folders_scanned):
        assert num_user_or_group_folders_scanned > 0

    def found_dataset(folder):
        folders.append(folder)

    with requests_mock.Mocker() as mocker:
        get_user_api_url = "%s/api/v1/user/?format=json&username=testfacility" % SETTINGS.general.mytardis_url
        mocker.get(get_user_api_url, text=MOCK_USER_RESPONSE)
        get_facility_api_url = "%s/api/v1/facility/?format=json" % SETTINGS.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument" % SETTINGS.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)

        scan_folders(found_user_or_group, found_dataset)

    assert sorted([folder.name for folder in folders]) == ["Birds", "Flowers"]
    assert sum([folder.num_files for folder in folders]) == 5
