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
    mock_testusers_response,
    mock_invalid_user_response,
    mock_test_facility_response,
    mock_test_instrument_response,
    mock_exp_creation,
    EMPTY_LIST_RESPONSE,
    created_dataset_response,
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
        mock_testusers_response(mocker, settings, ["testuser1", "testuser2"])
        mock_invalid_user_response(mocker, settings)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

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
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)
        for username, name in [
            ("testuser1", "Test User1"),
            ("testuser2", "Test User2"),
            ("INVALID_USER", "INVALID_USER (USER NOT FOUND IN MYTARDIS)"),
        ]:
            title = "Test Instrument - %s" % name
            user_folder_name = username
            mock_exp_creation(mocker, settings, title, user_folder_name)

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
            mock_dataset_response = created_dataset_response(1, folder.name)
            mocker.post(post_dataset_url, text=mock_dataset_response)
            upload_folder(
                folder, lookup_callback, upload_callback, UploadMethod.MULTIPART_POST
            )

        # Ensure that all 12 files were looked up:
        assert len(lookups) == 12

        # Ensure that all 12 files were uploaded:
        assert len(uploads) == 12
