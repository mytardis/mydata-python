"""
tests/commands/scan/test_scan_group_exp_dataset.py
"""
import textwrap

import requests_mock

from click.testing import CliRunner

from tests.fixtures import set_group_exp_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    mock_get_group,
    mock_test_facility_response,
    mock_test_instrument_response,
)


def test_scan_group_exp_dataset(set_group_exp_dataset_config):
    from mydata.commands.scan import scan_cmd
    from mydata.conf import settings

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        for group_name in ("TestFacility-Group1", "TestFacility-Group2"):
            mock_get_group(mocker, settings.general.mytardis_url, group_name)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        runner = CliRunner()
        result = runner.invoke(scan_cmd, [])
        assert result.exit_code == 0
        assert result.output == "%s\n" % textwrap.dedent(
            """
            Scanning tests/testdata/testdata-group-exp-dataset/ using the "User Group / Experiment / Dataset" folder structure...

            Found group folder: Group1
            Found group folder: Group2

            Found 2 dataset folders in tests/testdata/testdata-group-exp-dataset/

            Datasets will be collected into 2 experiments.
            """
        )
