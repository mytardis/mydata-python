"""
Test ability to scan the Username / Dataset folder structure
and upload using the SCP protocol.

This module provides the "test_scan_username_dataset_folders" function,
preceded by a series of helper functions.
"""
# pylint: disable=unused-import

import os

from string import Template
from urllib.parse import quote

import requests_mock

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
    mock_test_facility_response,
    mock_test_instrument_response,
    mock_exp_creation,
    mock_uploader_creation_response,
    mock_uploader_update_response,
    mock_get_urr,
    EMPTY_LIST_RESPONSE,
    CREATED_DATASET_RESPONSE,
    EXISTING_EXP_RESPONSE,
    EXISTING_DATASET_RESPONSE,
)


def upload_uploader_info(settings, mock_key_pair):
    """Create an Uploader record for this MyData instance
    """
    # pylint: disable=redefined-outer-name

    # Firstly, let's test the case where we don't have an existing uploader
    # record, i.e. the GET query will return an empty list, so, we'll
    # need to create a new uploader record with POST:

    # Reset global settings' uploader instance, so we when we next call
    # the settings.uploader property method, we'll generate a
    # new Uploader instance, using the up-to-date
    # settings.general.instrument_name:
    settings.uploader = None
    with requests_mock.Mocker() as mocker:
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)
        mock_uploader_creation_response(mocker, settings)
        settings.uploader.upload_uploader_info()
    assert settings.uploader.name == "Test Instrument"

    # Now let's test the case where we have an existing uploader record:

    # Reset global settings' uploader instance, so we when we next call
    # the settings.uploader property method, we'll generate a
    # new Uploader instance, using the up-to-date
    # settings.general.instrument_name:
    settings.uploader = None
    with requests_mock.Mocker() as mocker:
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)
        mock_uploader_update_response(mocker, settings)
        settings.uploader.upload_uploader_info()
    assert settings.uploader.name == "Test Instrument"

    settings.uploader.ssh_key_pair = mock_key_pair


def create_exp_and_dataset(folder, settings):
    """
    Creating the experiment and dataset for the folder will be done
    automatically when calling upload_folder, but for the mocked API
    responses we want to provide in this test, it is easier to
    explicitly create the experiment and dataset here:
    """
    from mydata.models.experiment import Experiment
    from mydata.models.dataset import Dataset

    with requests_mock.Mocker() as mocker:
        mock_exp_creation(
            mocker, settings, folder.experiment_title, folder.user_folder_name
        )
        get_dataset_url = (
            "%s/api/v1/dataset/?format=json&experiments__id=1"
            "&description=%s&instrument__id=1"
        ) % (settings.general.mytardis_url, quote(folder.name))
        mocker.get(get_dataset_url, text=EMPTY_LIST_RESPONSE)
        post_dataset_url = "%s/api/v1/dataset/" % settings.general.mytardis_url
        mock_dataset_response = CREATED_DATASET_RESPONSE.replace(
            "Created Dataset", folder.name
        )
        mocker.post(post_dataset_url, text=mock_dataset_response)
        folder.experiment = Experiment.get_or_create_exp_for_folder(folder)
        folder.dataset = Dataset.create_dataset_if_necessary(folder)


def mock_exp_lookups(mocker, settings):
    """Mock the experiment lookup for each expected user folder
    """
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
            text=EXISTING_EXP_RESPONSE.replace("Existing Experiment", name),
        )


def mock_datafiles_creation(mocker, folder, settings, mock_staging_path):
    """Mock datafile lookups and creation
    """
    # pylint: disable=redefined-outer-name
    get_dataset_url = (
        "%s/api/v1/dataset/?format=json&experiments__id=1"
        "&description=%s&instrument__id=1"
    ) % (settings.general.mytardis_url, quote(folder.name))
    mocker.get(
        get_dataset_url,
        text=EXISTING_DATASET_RESPONSE.replace("Existing Dataset", folder.name),
    )

    get_df_url_template = Template(
        (
            "%s/api/v1/mydata_dataset_file/?format=json&dataset__id=1"
            "&filename=$filename&directory="
        )
        % settings.general.mytardis_url
    )

    # For now, mocking of DataFile creation always creates
    # a Datafile with ID = 1:
    verify_url = "%s/api/v1/dataset_file/1/verify/" % settings.general.mytardis_url
    mocker.get(verify_url)

    for dfi in range(0, folder.num_files):
        datafile_path = folder.get_datafile_path(dfi)
        datafile_dir = folder.get_datafile_directory(dfi)
        datafile_name = os.path.basename(datafile_path)
        get_datafile_url = get_df_url_template.substitute(filename=quote(datafile_name))
        mocker.get(get_datafile_url, text=EMPTY_LIST_RESPONSE)
        post_datafile_url = (
            "%s/api/v1/mydata_dataset_file/" % settings.general.mytardis_url
        )
        temp_url = ""
        if folder.dataset:
            if datafile_dir:
                temp_url = "%s/DatasetDescription-%s/%s/%s" % (
                    mock_staging_path,
                    folder.dataset.id,
                    datafile_dir,
                    datafile_name,
                )
            else:
                temp_url = "%s/DatasetDescription-%s/%s" % (
                    mock_staging_path,
                    folder.dataset.id,
                    datafile_name,
                )
        # For now, mocking of DataFile creation always creates
        # a Datafile with ID = 1:
        mocker.post(
            post_datafile_url,
            status_code=201,
            text=temp_url,
            headers={"Location": "/api/v1/mydata_dataset_file/1/"},
        )


def mock_responses_for_scan_folders(mocker, settings):
    """Mock API responses needed when scanning folders
    for Username / Dataset folder structure
    """
    mock_testfacility_user_response(mocker, settings.general.mytardis_url)
    mock_testusers_response(mocker, settings, ["testuser1", "testuser2"])
    mock_invalid_user_response(mocker, settings)
    mock_test_facility_response(mocker, settings.general.mytardis_url)
    mock_test_instrument_response(mocker, settings.general.mytardis_url)


def mock_responses_for_upload_folders(
    folders, mocker, settings, mock_staging_path, mock_scp_server
):
    """Mock API responses needed when uploading folders
    for Username / Dataset folder structure,
    using SCP upload method.
    """
    # pylint: disable=redefined-outer-name

    mock_test_facility_response(mocker, settings.general.mytardis_url)
    mock_test_instrument_response(mocker, settings.general.mytardis_url)
    mock_exp_lookups(mocker, settings)

    mock_uploader_update_response(mocker, settings)
    _, scp_port = mock_scp_server.server_address
    mock_get_urr(mocker, settings, settings.uploader.ssh_key_pair.fingerprint, scp_port)

    for folder in folders:
        mock_datafiles_creation(mocker, folder, settings, mock_staging_path)


def assert_expected_user_folders(users):
    """Assert that we found the expected user folders
    """
    assert sorted([user.username for user in users]) == [
        "INVALID_USER",
        "testuser1",
        "testuser2",
    ]


def assert_expected_dataset_folders(folders):
    """Assert that we found the expected dataset folders
    """
    expected_folders = [
        "Birds",
        "Dataset with spaces",
        "Flowers",
        "InvalidUserDataset1",
    ]
    assert sorted([folder.name for folder in folders]) == expected_folders
    assert sum([folder.num_files for folder in folders]) == 12


def assert_expected_datafile_lookups(lookups):
    """Ensure that all 12 files were looked up:
    """
    from mydata.models.lookup import LookupStatus

    assert len(lookups) == 12

    for lookup in lookups:
        msg = "File: %s had unexpected lookup result: %s" % (
            lookup.filename,
            lookup.message,
        )
        assert lookup.status == LookupStatus.NOT_FOUND, msg


def assert_expected_datafile_uploads(uploads):
    """Ensure that all 12 files were uploaded
    """
    from mydata.models.upload import UploadStatus

    assert len(uploads) == 12

    for upload in uploads:
        msg = "%s: %s" % (upload.filename, upload.message)
        assert upload.status == UploadStatus.COMPLETED, msg


def assert_scan_folders_success(settings):
    """Test scanning folders in the Username / Dataset folder structure
    and assert that the results look OK.

    This is a helper function for test_scan_username_dataset_folders
    """
    from mydata.tasks.folders import scan_folders

    users = []
    folders = []

    def found_user(user):
        """When a user folder is found, add the User instance to a list
        """
        users.append(user)

    def found_dataset_folder(folder):
        """When a dataset folder is found, add the Folder instance to a list
        and create the required experiment and dataset for it if necessary.
        """
        folders.append(folder)

        create_exp_and_dataset(folder, settings)

    with requests_mock.Mocker() as mocker:
        mock_responses_for_scan_folders(mocker, settings)

        scan_folders(
            found_user,
            found_group_cb=None,
            found_exp_folder_cb=None,
            found_dataset_cb=found_dataset_folder,
        )

    assert_expected_user_folders(users)
    assert_expected_dataset_folders(folders)

    return folders


def assert_upload_folders_success(
    folders, settings, mock_scp_server, mock_staging_path
):
    """Test uploading folders in the Username / Dataset folder structure
    using the SCP upload method and assert that the results look OK.

    This is a helper function for test_scan_username_dataset_folders
    """
    # pylint: disable=redefined-outer-name

    from mydata.tasks.uploads import upload_folder
    from mydata.models.upload import UploadMethod

    with requests_mock.Mocker() as mocker:
        mock_responses_for_upload_folders(
            folders, mocker, settings, mock_staging_path, mock_scp_server
        )

        lookups = []
        uploads = []

        def lookup_callback(lookup):
            lookups.append(lookup)

        def upload_callback(upload):
            uploads.append(upload)

        for folder in folders:
            upload_folder(
                folder, lookup_callback, upload_callback, upload_method=UploadMethod.SCP
            )

        assert_expected_datafile_lookups(lookups)
        assert_expected_datafile_uploads(uploads)


def test_scan_username_dataset_folders(
    set_username_dataset_config, mock_scp_server, mock_key_pair, mock_staging_path
):
    """Test ability to scan the Username / Dataset folder structure.
    """
    # pylint: disable=redefined-outer-name,unused-argument

    from mydata.conf import settings

    upload_uploader_info(settings, mock_key_pair)

    folders = assert_scan_folders_success(settings)

    assert_upload_folders_success(folders, settings, mock_scp_server, mock_staging_path)
