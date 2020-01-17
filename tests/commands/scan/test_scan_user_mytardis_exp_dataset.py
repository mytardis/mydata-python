"""
tests/commands/scan/test_scan_user_mytardis_exp_dataset.py
"""
import textwrap

import requests_mock

from click.testing import CliRunner

from tests.fixtures import set_user_mytardis_exp_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    mock_test_facility_response,
    mock_test_instrument_response,
    mock_testusers_response,
)


def test_scan_user_mytardis_exp_dataset(set_user_mytardis_exp_dataset_config):
    from mydata.commands.scan import scan_cmd
    from mydata.conf import settings

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        mock_testusers_response(
            mocker, settings, ["testuser1", "testuser2", "testuser3"]
        )
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        runner = CliRunner()
        result = runner.invoke(scan_cmd, [])
        assert result.exit_code == 0
        assert result.output == "%s\n" % textwrap.dedent(
            """
            Scanning tests/testdata/testdata-user-mytardis-exp-dataset/ using the "Username / "MyTardis" / Experiment / Dataset" folder structure...

            Found user folder: testuser1
            Found user folder: testuser2
            Found user folder: testuser3

            Found 2 dataset folders in tests/testdata/testdata-user-mytardis-exp-dataset/

            Datasets will be collected into 2 experiments.
            """
        )
