"""
Test indexing of already-uploaded data
"""
# pylint: disable=line-too-long
import os
import textwrap

from string import Template
from urllib.parse import quote

import requests_mock

from click.testing import CliRunner

from tests.mocks import (
    mock_testfacility_user_response,
    mock_birds_flowers_datafile_lookups,
    CREATED_DATASET_RESPONSE,
    EMPTY_LIST_RESPONSE,
)


def test_indexing():
    """
    Test indexing of already-uploaded data
    """
    from mydata.commands.index import index_cmd

    env = dict(
        MYTARDIS_URL="https://www.example.com",
        MYTARDIS_USERNAME="testfacility",
        MYTARDIS_API_KEY="mock_api_key",
        MYTARDIS_STORAGE_BOX_PATH=os.path.abspath(
            os.path.join(".", "tests", "testdata", "testdata-dataset")
        ),
        MYTARDIS_STORAGE_BOX_NAME="storage-box1",
        MYTARDIS_SRC_PATH=os.path.abspath(
            os.path.join(".", "tests", "testdata", "testdata-dataset")
        ),
        MYTARDIS_EXP_ID="123",
    )

    runner = CliRunner()

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, env["MYTARDIS_URL"])
        mock_birds_flowers_datafile_lookups(mocker)
        for folder_name in ("Birds", "Flowers"):
            folder_path = os.path.join(env["MYTARDIS_STORAGE_BOX_PATH"], folder_name)

            get_dataset_url = (
                "%s/api/v1/dataset/?format=json&experiments__id=123" "&description=%s"
            ) % (env["MYTARDIS_URL"], quote(folder_name))
            mocker.get(get_dataset_url, text=EMPTY_LIST_RESPONSE)

            post_dataset_url = "%s/api/v1/dataset/" % env["MYTARDIS_URL"]
            mock_dataset_response = CREATED_DATASET_RESPONSE.replace(
                "Created Dataset", folder_name
            )
            mocker.post(post_dataset_url, text=mock_dataset_response)

            post_datafile_url = "%s/api/v1/dataset_file/" % env["MYTARDIS_URL"]
            mocker.post(
                post_datafile_url,
                status_code=201,
                headers=dict(Location="/api/v1/dataset_file/123456"),
            )

            result = runner.invoke(
                index_cmd, [folder_path], env=env, catch_exceptions=False
            )
            assert result.exit_code == 0

            expected_output_template = Template(
                "%s\n"
                % textwrap.dedent(
                    """
                MYTARDIS_STORAGE_BOX_PATH: $cwd/tests/testdata/testdata-dataset

                Validated MyTardis settings.

                Indexing folder: $folder_name

                Created Dataset record for '$folder_name' with ID: 1

                $files
                """
                )
            )
            expected_files_output_template = {
                "Birds": Template(
                    textwrap.dedent(
                        """\
                    File path: $cwd/tests/testdata/testdata-dataset/Birds/1024px-Australian_Birds_@_Jurong_Bird_Park_(4374195521).jpg
                    size: 116537
                    mimetype: image/jpeg
                    md5sum: 53c6ac03b64f61d5e0b596f70ed75a51

                    Created DataFile record: /api/v1/dataset_file/123456


                    File path: $cwd/tests/testdata/testdata-dataset/Birds/Black-beaked-sea-bird-close-up.jpg
                    Failed to check for existing DataFile record on MyTardis.  Skipping for now.

                    1 of 2 files have been indexed by MyTardis.
                    0 of 2 files have been verified by MyTardis.
                    1 of 2 files were newly indexed in this session.
                    """
                    )
                ),
                "Flowers": Template(
                    textwrap.dedent(
                        """\
                    File path: $cwd/tests/testdata/testdata-dataset/Flowers/1024px-Colourful_flowers.JPG
                    DataFile record was found, so we won't create another record for this file.

                    File path: $cwd/tests/testdata/testdata-dataset/Flowers/Flowers_growing_on_the_campus_of_Cebu_City_National_Science_High_School.jpg
                    DataFile record was found, so we won't create another record for this file.

                    File path: $cwd/tests/testdata/testdata-dataset/Flowers/Pond_Water_Hyacinth_Flowers.jpg
                    size: 341543
                    mimetype: image/jpeg
                    md5sum: 4eecf4d4b352c6a12100013a6ad2474a

                    Created DataFile record: /api/v1/dataset_file/123456


                    3 of 3 files have been indexed by MyTardis.
                    2 of 3 files have been verified by MyTardis.
                    1 of 3 files were newly indexed in this session.

                    File records on server without any DataFileObjects:
                    Dataset ID: 1, Filename: Pond_Water_Hyacinth_Flowers.jpg
                    """
                    )
                ),
            }
            expected_files_output = expected_files_output_template[
                folder_name
            ].substitute(cwd=os.getcwd())
            assert result.output == expected_output_template.substitute(
                folder_name=folder_name, files=expected_files_output, cwd=os.getcwd()
            )


def test_indexing_missing_settings():
    """
    Test attempt to run indexing without providing settings

    Setting environment variables to an empty string means
    that the indexing code will treat them as falsy, irrespective
    of whether the developer or tester has a .env file in the current
    directory which would be read by dotenv.load_dotenv()
    """
    from mydata.commands.index import index_cmd

    env = dict(
        MYTARDIS_URL="",
        MYTARDIS_USERNAME="",
        MYTARDIS_API_KEY="",
        MYTARDIS_STORAGE_BOX_PATH="",
        MYTARDIS_STORAGE_BOX_NAME="",
        MYTARDIS_SRC_PATH="",
        MYTARDIS_EXP_ID="",
    )
    runner = CliRunner()
    result = runner.invoke(index_cmd, ["."], env=env, catch_exceptions=False)
    assert result.exit_code == 1
    assert result.output == textwrap.dedent(
        """\
        Missing parameter(s):
        Set a MyTardis URL with MYTARDIS_URL
        Set a MyTardis username with MYTARDIS_USERNAME
        Set a MyTardis API key with MYTARDIS_API_KEY
        Set a MyTardis experiment ID with MYTARDIS_EXP_ID
        Set a MyTardis storage box name with MYTARDIS_STORAGE_BOX_NAME
        Set a MyTardis storage box path with MYTARDIS_STORAGE_BOX_PATH
        Set a data source path with MYTARDIS_SRC_PATH
    """
    )
