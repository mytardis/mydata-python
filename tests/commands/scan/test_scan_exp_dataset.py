"""
tests/commands/scan/test_scan_exp_dataset.py
"""
import textwrap

import requests_mock

from click.testing import CliRunner

from tests.fixtures import set_exp_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE,
)


def test_scan_exp_dataset(set_exp_dataset_config):
    from mydata.commands.scan import scan_cmd
    from mydata.conf import settings

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        get_facility_api_url = (
            "%s/api/v1/facility/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1"
            "&name=Test%%20Instrument"
        ) % settings.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)

        runner = CliRunner()
        result = runner.invoke(scan_cmd, [])
        assert result.exit_code == 0
        assert result.output == "%s\n" % textwrap.dedent(
            """
            Scanning tests/testdata/testdata-exp-dataset/ using the "Experiment / Dataset" folder structure...
            
            Found 2 dataset folders in tests/testdata/testdata-exp-dataset/

            Datasets will be collected into 2 experiments.
            """
        )
