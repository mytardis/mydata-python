"""
tests/commands/upload/test_upload_exp_dataset_structure.py

Tests for uploading files from within the "Experiment / Dataset" folder structure
"""
import json
import textwrap

import requests_mock

from click.testing import CliRunner

from tests.fixtures import set_exp_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    mock_test_facility_response,
    mock_test_instrument_response,
    EMPTY_LIST_RESPONSE,
    CREATED_EXP_RESPONSE,
    CREATED_DATASET_RESPONSE,
    EXISTING_DATASET_RESPONSE,
    VERIFIED_DATAFILE_RESPONSE,
)


def test_upload_exp_dataset_structure(set_exp_dataset_config):
    """Test uploading files from within the "Experiment / Dataset" folder structure
    """
    from mydata.commands.upload import upload_cmd
    from mydata.conf import settings

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        for title in ("Exp1", "Exp2"):
            get_exp_url = (
                "%s/api/v1/mydata_experiment/?format=json"
                "&title=%s"
                "&folder_structure=Experiment%%20/%%20Dataset&user_folder_name=testfacility"
            ) % (settings.general.mytardis_url, title)
            mocker.get(get_exp_url, text=EMPTY_LIST_RESPONSE)
        post_experiment_url = (
            "%s/api/v1/mydata_experiment/" % settings.general.mytardis_url
        )
        mocker.post(post_experiment_url, text=CREATED_EXP_RESPONSE)
        post_objectacl_url = "%s/api/v1/objectacl/" % settings.general.mytardis_url
        mocker.post(post_objectacl_url, status_code=201)

        # A partial query-string match can be used for mocking:
        get_birds_dataset_url = (
            "/api/v1/dataset/?format=json&experiments__id=1&description=Birds"
        )
        mocker.get(get_birds_dataset_url, text=EMPTY_LIST_RESPONSE)
        get_flowers_dataset_url = (
            "/api/v1/dataset/?format=json&experiments__id=1&description=Flowers"
        )
        mocker.get(
            get_flowers_dataset_url,
            text=EXISTING_DATASET_RESPONSE.replace("Existing Dataset", "Flowers"),
        )

        post_dataset_url = "%s/api/v1/dataset/" % settings.general.mytardis_url
        # Response really should be different for each dataset,
        # but that would complicate mocking:
        mocker.post(post_dataset_url, text=CREATED_DATASET_RESPONSE)

        # A partial query-string match can be used for mocking:
        for filename in (
            "1024px-Colourful_flowers.JPG",
            "Flowers_growing_on_the_campus_of_Cebu_City_National_Science_High_School.jpg",
            "Pond_Water_Hyacinth_Flowers.jpg",
        ):
            get_datafile_url = (
                "/api/v1/mydata_dataset_file/?format=json&dataset__id=1&filename=%s"
                % filename
            )
            mocker.get(
                get_datafile_url,
                text=VERIFIED_DATAFILE_RESPONSE.replace("Verified File", filename),
            )
        for filename in (
            "1024px-Australian_Birds_%40_Jurong_Bird_Park_%284374195521%29.jpg",
        ):
            get_datafile_url = (
                "/api/v1/mydata_dataset_file/?format=json&dataset__id=1&filename=%s"
                % filename
            )
            mocker.get(get_datafile_url, text=EMPTY_LIST_RESPONSE)
        for filename in ("Black-beaked-sea-bird-close-up.jpg",):
            get_datafile_url = (
                "/api/v1/mydata_dataset_file/?format=json&dataset__id=1&filename=%s"
                % filename
            )
            error_response = json.dumps({"error_message": "Internal Server Error"})
            mocker.get(get_datafile_url, text=error_response, status_code=500)

        post_datafile_url = "/api/v1/mydata_dataset_file/"
        mocker.post(post_datafile_url, status_code=201)

        runner = CliRunner()
        result = runner.invoke(upload_cmd, ["-vv"])
        if result.exception:
            raise result.exception
        assert result.exit_code == 0
        assert result.output.startswith(
            textwrap.dedent(
                """
            Using MyData configuration in: %s

            Scanning tests/testdata/testdata-exp-dataset/ using the "Experiment / Dataset" folder structure...

            Found 2 dataset folders in tests/testdata/testdata-exp-dataset/

            Datasets will be collected into 2 experiments.
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
