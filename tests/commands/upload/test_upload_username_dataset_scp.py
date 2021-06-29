"""
tests/commands/upload/test_upload_username_dataset_scp.py

Test ability to scan the Username / Dataset folder structure
and upload using the SCP protocol.
"""
import os
import textwrap

from unittest.mock import Mock

import requests_mock

from click.testing import CliRunner

from mydata.models.localfile import LocalFile

from tests.fixtures import (
    set_username_dataset_config,
    mock_scp_server,
    mock_key_pair,
    mock_staging_path,
)

from tests.mocks import (
    mock_testfacility_user_response,
    mock_testusers_response,
    mock_invalid_user_response,
    mock_birds_flowers_dataset_creation,
    mock_dataset_creation,
)

from tests.uploads.test_username_dataset_scp import (
    upload_uploader_info,
    mock_responses_for_upload_folders,
)


def test_upload_username_dataset_scp(
    set_username_dataset_config, mock_scp_server, mock_key_pair, mock_staging_path
):
    """Test ability to scan the Username / Dataset folder structure
    and upload using the SCP protocol.
    """
    from mydata.commands.upload import upload_cmd
    from mydata.conf import settings

    upload_uploader_info(settings, mock_key_pair)

    data_dir = settings.general.data_directory

    filenames = {
        "Flowers": os.listdir(os.path.join(data_dir, "testuser1", "Flowers")),
        "Birds": os.listdir(os.path.join(data_dir, "testuser2", "Birds")),
        "Dataset with spaces": os.listdir(
            os.path.join(data_dir, "testuser1", "Dataset with spaces")
        ),
        "InvalidUserDataset1": os.listdir(
            os.path.join(data_dir, "INVALID_USER", "InvalidUserDataset1")
        ),
    }
    folders = []
    for folder_name in filenames:
        folder = Mock()
        folder.dataset = Mock(id=1)
        folder.name = folder_name
        folder.num_files = len(filenames[folder_name])
        folder.local_files = []
        for filename in filenames[folder_name]:
            folder.local_files.append(LocalFile(filename, "", False))
        folders.append(folder)

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        mock_testusers_response(mocker, settings, ["testuser1", "testuser2"])
        mock_invalid_user_response(mocker, settings)
        mock_birds_flowers_dataset_creation(mocker, settings)
        for folder in folders:
            exp_id = 1
            instrument_id = 1
            mock_dataset_creation(mocker, settings, exp_id, instrument_id, folder.name)
        mock_responses_for_upload_folders(
            folders, mocker, settings, mock_staging_path, mock_scp_server
        )
        runner = CliRunner()
        result = runner.invoke(upload_cmd, ["-vv"])
        if result.exception:
            raise result.exception
        assert result.exit_code == 0
        assert result.output.strip() == textwrap.dedent(
            """
            Using MyData configuration in: %s

            Scanning tests/testdata/testdata-username-dataset/ using the "Username / Dataset" folder structure...

            Checking for approved upload method...

            Using SCP upload method.

            Found user folder: INVALID_USER [USER "INVALID_USER" WAS NOT FOUND ON THE MYTARDIS SERVER]
            Found user folder: testuser1
            Found user folder: testuser2

            Found 4 dataset folders in tests/testdata/testdata-username-dataset/

            Data in Birds/ is being archived to http://127.0.0.1:9000/dataset/1
            Data in Dataset with spaces/ is being archived to http://127.0.0.1:9000/dataset/1
            Data in Flowers/ is being archived to http://127.0.0.1:9000/dataset/1
            Data in InvalidUserDataset1/ is being archived to http://127.0.0.1:9000/dataset/1

            12 of 12 files have been uploaded to MyTardis.
            0 of 12 files have been verified by MyTardis.
            12 of 12 files were newly uploaded in this session.
            0 of 12 file lookups were found in the local cache.

            Not found on MyTardis server:
            1024px-Australian_Birds_@_Jurong_Bird_Park_(4374195521).jpg
            1024px-Colourful_flowers.JPG
            Black-beaked-sea-bird-close-up.jpg
            Flowers_growing_on_the_campus_of_Cebu_City_National_Science_High_School.jpg
            InvalidUserFile1.txt
            Pond_Water_Hyacinth_Flowers.jpg
            existing_unverified_full_size_file.txt
            existing_unverified_incomplete_file.txt
            existing_verified_file.txt
            hello.txt
            missing_mydata_replica_api_endpoint.txt
            zero_sized_file.txt

            Files uploaded:
            1024px-Australian_Birds_@_Jurong_Bird_Park_(4374195521).jpg [Completed]
            1024px-Colourful_flowers.JPG [Completed]
            Black-beaked-sea-bird-close-up.jpg [Completed]
            Flowers_growing_on_the_campus_of_Cebu_City_National_Science_High_School.jpg [Completed]
            InvalidUserFile1.txt [Completed]
            Pond_Water_Hyacinth_Flowers.jpg [Completed]
            existing_unverified_full_size_file.txt [Completed]
            existing_unverified_incomplete_file.txt [Completed]
            existing_verified_file.txt [Completed]
            hello.txt [Completed]
            missing_mydata_replica_api_endpoint.txt [Completed]
            zero_sized_file.txt [Completed]

           """
            % settings.config_path
        ).strip()
