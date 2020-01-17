"""
tests/commands/upload/test_upload_dataset_structure.py

Tests for uploading files from within the "Dataset" folder structure
"""
import textwrap

import requests_mock

from click.testing import CliRunner

from tests.fixtures import set_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    mock_test_facility_response,
    mock_test_instrument_response,
    mock_birds_flowers_dataset_creation,
    mock_birds_flowers_datafile_lookups,
    mock_exp_creation,
    EMPTY_LIST_RESPONSE,
)


def test_upload_dataset_structure(set_dataset_config):
    """Test uploading files from within the "Dataset" folder structure
    """
    from mydata.commands.upload import upload_cmd
    from mydata.conf import settings

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        mock_exp_creation(
            mocker,
            settings,
            "Test Instrument - TestFacility RoleAccount",
            user_folder_name="testfacility",
        )

        mock_birds_flowers_dataset_creation(mocker, settings)

        mock_birds_flowers_datafile_lookups(mocker)

        runner = CliRunner()
        result = runner.invoke(upload_cmd, ["-vv"])
        if result.exception:
            raise result.exception
        assert result.exit_code == 0
        assert result.output.startswith(
            textwrap.dedent(
                """
            Using MyData configuration in: %s

            Scanning tests/testdata/testdata-dataset/ using the "Dataset" folder structure...

            Found 2 dataset folders in tests/testdata/testdata-dataset/
            """
                % settings.config_path
            )
        )
        assert result.output.endswith(
            textwrap.dedent(
                """\
                4 of 5 files have been uploaded to MyTardis.
                3 of 5 files have been verified by MyTardis.
                1 of 5 files were newly uploaded in this session.
                0 of 5 file lookups were found in the local cache.

                Failed lookups:
                Black-beaked-sea-bird-close-up.jpg

                Not found on MyTardis server:
                1024px-Australian_Birds_@_Jurong_Bird_Park_(4374195521).jpg

                Files uploaded:
                1024px-Australian_Birds_@_Jurong_Bird_Park_(4374195521).jpg [Completed]

            """
            )
        )
