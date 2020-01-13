"""
tests/commands/scan/test_scan_user_exp_dataset.py
"""
import textwrap

import requests_mock

from click.testing import CliRunner

from tests.fixtures import set_user_exp_dataset_config

from tests.mocks import (
    MOCK_USER_RESPONSE,
    MOCK_TESTUSER1_RESPONSE,
    MOCK_TESTUSER2_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE,
)


def test_scan_user_exp_dataset(set_user_exp_dataset_config):
    from mydata.commands.scan import scan_cmd
    from mydata.conf import settings

    with requests_mock.Mocker() as mocker:
        get_user_api_url = (
            "%s/api/v1/user/?format=json&username=testfacility"
            % settings.general.mytardis_url
        )
        mocker.get(get_user_api_url, text=MOCK_USER_RESPONSE)
        get_testuser1_url = (
            "%s/api/v1/user/?format=json&username=testuser1"
        ) % settings.general.mytardis_url
        mocker.get(get_testuser1_url, text=MOCK_TESTUSER1_RESPONSE)
        get_testuser2_url = get_testuser1_url.replace("testuser1", "testuser2")
        mocker.get(get_testuser2_url, text=MOCK_TESTUSER2_RESPONSE)
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
            """\
            Scanning tests/testdata/testdata-user-exp-dataset/ using the "Username / Experiment / Dataset" folder structure...

            Found user folder: testuser1
            Found user folder: testuser2

            Found 2 dataset folders in tests/testdata/testdata-user-exp-dataset/

            Datasets will be collected into 2 experiments.
            """
        )
