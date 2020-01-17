"""
Test ability to scan the Group / Instrument folder structure.
"""
import requests_mock

from tests.fixtures import set_group_instrument_config

from tests.mocks import (
    mock_testfacility_user_response,
    MOCK_GROUP_RESPONSE,
    MOCK_GROUP2_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE,
)


def test_scan_group_instrument_folders(set_group_instrument_config):
    """Test ability to scan the Group / Instrument folder structure.
    """
    from mydata.conf import settings
    from mydata.tasks.folders import scan_folders

    groups = []
    folders = []

    # We don't need callback for these:
    found_exp = None
    found_user = None

    def found_group(group):
        groups.append(group)

    def found_dataset(folder):
        folders.append(folder)

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        get_group1_url = (
            "%s/api/v1/group/?format=json&name=TestFacility-Group1"
            % settings.general.mytardis_url
        )
        mocker.get(get_group1_url, text=MOCK_GROUP_RESPONSE)
        get_group2_url = get_group1_url.replace("Group1", "Group2")
        mocker.get(get_group2_url, text=MOCK_GROUP2_RESPONSE)
        get_facility_api_url = (
            "%s/api/v1/facility/?format=json" % settings.general.mytardis_url
        )
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument"
            % settings.general.mytardis_url
        )
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)

        scan_folders(found_user, found_group, found_exp, found_dataset)

    assert sorted([group.name for group in groups]) == [
        "TestFacility-Group1",
        "TestFacility-Group2",
    ]
    assert sorted([folder.name for folder in folders]) == [
        "Dataset 001",
        "Dataset 002",
        "Dataset 003",
        "Dataset 004",
        "Dataset 005",
        "Dataset 006",
        "Dataset 007",
        "Dataset 008",
    ]

    assert sum([folder.num_files for folder in folders]) == 8
