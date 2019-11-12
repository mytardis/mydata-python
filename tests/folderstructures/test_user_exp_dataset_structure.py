"""
Test ability to scan the Username / Experiment / Dataset folder structure.
"""
import requests_mock

from tests.fixtures import set_user_exp_dataset_config

from tests.mocks import (
    MOCK_USER_RESPONSE,
    MOCK_TESTUSER1_RESPONSE,
    MOCK_TESTUSER2_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE
)

def test_scan_user_exp_dataset_folders(set_user_exp_dataset_config):
    """Test ability to scan the Username / Experiment / Dataset folder structure.
    """
    from mydata.settings import SETTINGS
    from mydata.tasks import scan_folders

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
        get_user_api_url = "%s/api/v1/user/?format=json&username=testfacility" % SETTINGS.general.mytardis_url
        mocker.get(get_user_api_url, text=MOCK_USER_RESPONSE)
        get_testuser1_url = (
            "%s/api/v1/user/?format=json&username=testuser1"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_testuser1_url, text=MOCK_TESTUSER1_RESPONSE)
        get_testuser2_url = get_testuser1_url.replace("testuser1", "testuser2")
        mocker.get(get_testuser2_url, text=MOCK_TESTUSER2_RESPONSE)
        get_facility_api_url = "%s/api/v1/facility/?format=json" % SETTINGS.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument" % SETTINGS.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)

        scan_folders(found_user, found_group, found_exp, found_dataset)

    assert sorted([user.username for user in users]) == ["testuser1", "testuser2"]
    assert sorted(exps) == ["Exp1", "Exp2"]
    assert sorted([folder.name for folder in folders]) == ["Birds", "Flowers"]
    assert sum([folder.num_files for folder in folders]) == 5
