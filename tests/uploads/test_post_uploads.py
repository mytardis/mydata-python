"""
Test POST uploads
"""
import os

from string import Template
from urllib.parse import quote

import requests_mock

from tests.fixtures import set_username_dataset_config

from tests.mocks import (
    mock_testfacility_user_response,
    MOCK_TESTUSER1_RESPONSE,
    MOCK_TESTUSER2_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE,
    EMPTY_LIST_RESPONSE,
    CREATED_EXP_RESPONSE,
    CREATED_DATASET_RESPONSE,
)


def test_post_uploads(set_username_dataset_config):
    """
    Test POST uploads
    """
    from mydata.conf import settings
    from mydata.tasks.folders import scan_folders
    from mydata.tasks.uploads import upload_folder
    from mydata.models.lookup import LookupStatus
    from mydata.models.upload import UploadStatus, UploadMethod

    users = []
    folders = []

    def found_user(user):
        users.append(user)

    found_exp = None
    found_group = None

    def found_dataset(folder):
        folders.append(folder)

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        get_testuser1_url = (
            "%s/api/v1/user/?format=json&username=testuser1"
            % settings.general.mytardis_url
        )
        mocker.get(get_testuser1_url, text=MOCK_TESTUSER1_RESPONSE)
        get_testuser2_url = get_testuser1_url.replace("testuser1", "testuser2")
        mocker.get(get_testuser2_url, text=MOCK_TESTUSER2_RESPONSE)
        get_invalid_user_url = (
            "%s/api/v1/user/?format=json&username=INVALID_USER"
            % settings.general.mytardis_url
        )
        mocker.get(get_invalid_user_url, text=EMPTY_LIST_RESPONSE)
        get_facility_api_url = (
            "%s/api/v1/facility/?format=json" % settings.general.mytardis_url
        )
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument"
            % settings.general.mytardis_url
        )
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)

        scan_folders(found_user, found_group, found_exp, found_dataset)

    assert sorted([user.username for user in users]) == [
        "INVALID_USER",
        "testuser1",
        "testuser2",
    ]
    assert sorted([folder.name for folder in folders]) == [
        "Birds",
        "Dataset with spaces",
        "Flowers",
        "InvalidUserDataset1",
    ]
    assert sum([folder.num_files for folder in folders]) == 12

    with requests_mock.Mocker() as mocker:
        get_facility_api_url = (
            "%s/api/v1/facility/?format=json" % settings.general.mytardis_url
        )
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument"
            % settings.general.mytardis_url
        )
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)
        get_exp_url_template = Template(
            (
                "%s/api/v1/mydata_experiment/?format=json&title=Test%%20Instrument%%20-%%20$name"
                "&folder_structure=Username%%20/%%20Dataset&user_folder_name=$username"
            )
            % settings.general.mytardis_url
        )
        for username, name in [
            ("testuser1", quote("Test User1")),
            ("testuser2", quote("Test User2")),
            ("INVALID_USER", "INVALID_USER%20%28USER%20NOT%20FOUND%20IN%20MYTARDIS%29"),
        ]:
            mocker.get(
                get_exp_url_template.substitute(username=username, name=name),
                text=EMPTY_LIST_RESPONSE,
            )
        post_experiment_url = (
            "%s/api/v1/mydata_experiment/" % settings.general.mytardis_url
        )
        mocker.post(post_experiment_url, text=CREATED_EXP_RESPONSE)
        post_objectacl_url = "%s/api/v1/objectacl/" % settings.general.mytardis_url
        mocker.post(post_objectacl_url, status_code=201)
        for folder in folders:
            get_dataset_url = (
                "%s/api/v1/dataset/?format=json&experiments__id=1"
                "&description=%s&instrument__id=1"
            ) % (settings.general.mytardis_url, quote(folder.name))
            mocker.get(get_dataset_url, text=EMPTY_LIST_RESPONSE)

            get_df_url_template = Template(
                (
                    "%s/api/v1/mydata_dataset_file/?format=json&dataset__id=1&filename=$filename&directory="
                )
                % settings.general.mytardis_url
            )

            for dfi in range(0, folder.num_files):
                datafile_path = folder.get_datafile_path(dfi)
                datafile_name = os.path.basename(datafile_path)
                get_datafile_url = get_df_url_template.substitute(
                    filename=quote(datafile_name)
                )
                mocker.get(get_datafile_url, text=EMPTY_LIST_RESPONSE)

        post_dataset_url = "%s/api/v1/dataset/" % settings.general.mytardis_url

        post_datafile_url = (
            "%s/api/v1/mydata_dataset_file/" % settings.general.mytardis_url
        )
        mocker.post(post_datafile_url, status_code=201)

        lookups = []
        uploads = []

        def lookup_callback(lookup):
            msg = "File: %s had unexpected lookup result: %s" % (
                lookup.filename,
                lookup.message,
            )
            assert lookup.status == LookupStatus.NOT_FOUND, msg
            lookups.append(lookup)

        def upload_callback(upload):
            msg = "File: %s had unexpected upload result: %s" % (
                upload.filename,
                upload.message,
            )
            assert upload.status == UploadStatus.COMPLETED, msg
            uploads.append(upload)

        for folder in folders:
            mock_dataset_response = CREATED_DATASET_RESPONSE.replace(
                "Created Dataset", folder.name
            )
            mocker.post(post_dataset_url, text=mock_dataset_response)
            upload_folder(
                folder, lookup_callback, upload_callback, UploadMethod.MULTIPART_POST
            )

        # Ensure that all 12 files were looked up:
        assert len(lookups) == 12

        # Ensure that all 12 files were uploaded:
        assert len(uploads) == 12
