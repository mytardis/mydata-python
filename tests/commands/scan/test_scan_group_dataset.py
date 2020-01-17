"""
tests/commands/scan/test_scan_group_dataset.py
"""
import textwrap

import requests_mock

from click.testing import CliRunner

from tests.fixtures import set_group_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    MOCK_GROUP_RESPONSE,
    MOCK_GROUP2_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE,
)


def test_scan_group_dataset(set_group_dataset_config):
    from mydata.commands.scan import scan_cmd
    from mydata.conf import settings

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

        runner = CliRunner()
        result = runner.invoke(scan_cmd, [])
        assert result.exit_code == 0
        assert result.output == "%s\n" % textwrap.dedent(
            """
            Scanning tests/testdata/testdata-group-dataset/ using the "User Group / Dataset" folder structure...

            Found group folder: Group1
            Found group folder: Group2

            Found 2 dataset folders in tests/testdata/testdata-group-dataset/
            """
        )
