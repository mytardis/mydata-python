"""
Test ability to scan the Group / Experiment / Dataset folder structure.
"""
import requests_mock

from tests.fixtures import set_group_exp_dataset_config

from tests.mocks import (
    MOCK_USER_RESPONSE,
    MOCK_GROUP_RESPONSE,
    MOCK_GROUP2_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE
)

def test_scan_group_exp_dataset_folders(set_group_exp_dataset_config):
    """Test ability to scan the Group / Experiment / Dataset folder structure.
    """
    from mydata.settings import SETTINGS
    from mydata.tasks import scan_folders

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
        get_user_api_url = "%s/api/v1/user/?format=json&username=testfacility" % SETTINGS.general.mytardis_url
        mocker.get(get_user_api_url, text=MOCK_USER_RESPONSE)
        get_group1_url = "%s/api/v1/group/?format=json&name=TestFacility-Group1" % SETTINGS.general.mytardis_url
        mocker.get(get_group1_url, text=MOCK_GROUP_RESPONSE)
        get_group2_url = get_group1_url.replace("Group1", "Group2")
        mocker.get(get_group2_url, text=MOCK_GROUP2_RESPONSE)
        get_facility_api_url = "%s/api/v1/facility/?format=json" % SETTINGS.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument" % SETTINGS.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)

        scan_folders(found_user, found_group, found_exp, found_dataset)

    assert sorted([group.name for group in groups]) == ["TestFacility-Group1", "TestFacility-Group2"]
    assert sorted(exps) == ["Exp1", "Exp2"]
    assert sorted([folder.name for folder in folders]) == ["Birds", "Flowers"]
    assert sum([folder.num_files for folder in folders]) == 5
