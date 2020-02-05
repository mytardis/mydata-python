"""
tests/commands/upload/test_upload_email_dataset_structure.py

Tests for uploading files from within the "Email / Dataset" folder structure
"""
import textwrap

import requests_mock

from click.testing import CliRunner

from tests.fixtures import (
    set_email_dataset_config,
    mock_key_pair,
)

from tests.mocks import (
    mock_testfacility_user_response,
    mock_test_facility_response,
    mock_test_instrument_response,
    mock_testusers_response,
    mock_birds_flowers_dataset_creation,
    mock_birds_flowers_datafile_lookups,
    mock_exp_creation,
    mock_uploader_creation_response,
    mock_get_urr,
)


def test_upload_email_dataset_structure(set_email_dataset_config, mock_key_pair):
    """Test uploading files from within the "Email / Dataset" folder structure
    """
    from mydata.commands.upload import upload_cmd
    from mydata.conf import settings

    with requests_mock.Mocker() as mocker:
        mock_uploader_creation_response(mocker, settings)
        settings.uploader.ssh_key_pair = mock_key_pair
        mock_get_urr(mocker, settings, mock_key_pair.fingerprint, approved=False)
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        mock_testusers_response(mocker, settings, ["testuser1", "testuser2"])

        for user in ("testuser1", "testuser2"):
            name = "Test User1" if user == "testuser1" else "Test User2"
            title = "Test Instrument - %s" % name
            user_folder_name = "%s@example.com" % user
            mock_exp_creation(mocker, settings, title, user_folder_name)

        mock_birds_flowers_dataset_creation(mocker, settings)

        mock_birds_flowers_datafile_lookups(mocker, api_prefix="mydata_")

        runner = CliRunner()
        result = runner.invoke(upload_cmd, ["-vv"])
        if result.exception:
            raise result.exception
        assert result.exit_code == 0
        assert result.output == textwrap.dedent(
            """
                Using MyData configuration in: %s

                Scanning tests/testdata/testdata-email-dataset/ using the "Email / Dataset" folder structure...

                Checking for approved upload method...

                Using Multipart POST upload method.

                Found user folder: testuser1@example.com
                Found user folder: testuser2@example.com

                Found 2 dataset folders in tests/testdata/testdata-email-dataset/

                4 of 5 files have been uploaded to MyTardis.
                2 of 5 files have been verified by MyTardis.
                1 of 5 files were found unverified without any DataFileObjects! Contact server admins!
                2 of 5 files were newly uploaded in this session.
                0 of 5 file lookups were found in the local cache.

                File records on server without any DataFileObjects:
                Dataset ID: 1, Filename: Pond_Water_Hyacinth_Flowers.jpg

                Failed lookups:
                Black-beaked-sea-bird-close-up.jpg [500 Server Error: None for url: %s/api/v1/mydata_dataset_file/?format=json&dataset__id=1&filename=Black-beaked-sea-bird-close-up.jpg&directory=]

                Unverified lookups:
                Pond_Water_Hyacinth_Flowers.jpg

                Not found on MyTardis server:
                1024px-Australian_Birds_@_Jurong_Bird_Park_(4374195521).jpg

                Files uploaded:
                1024px-Australian_Birds_@_Jurong_Bird_Park_(4374195521).jpg [Completed]
                Pond_Water_Hyacinth_Flowers.jpg [Completed]

            """
            % (settings.config_path, settings.mytardis_url)
        )
