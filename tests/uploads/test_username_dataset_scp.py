"""
Test ability to scan the Username / Dataset folder structure.
"""
import os

from string import Template
from urllib.parse import quote

import requests_mock

from tests.fixtures import (
    set_username_dataset_config,
    mock_scp_server,
    mock_key_pair,
    mock_staging_path
)

from tests.mocks import (
    MOCK_USER_RESPONSE,
    MOCK_TESTUSER1_RESPONSE,
    MOCK_TESTUSER2_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE,
    EMPTY_LIST_RESPONSE,
    MOCK_UPLOADER_RESPONSE,
    MOCK_EXISTING_UPLOADER_RESPONSE,
    CREATED_EXP_RESPONSE,
    CREATED_DATASET_RESPONSE,
    MOCK_URR_RESPONSE,
    EXISTING_EXP_RESPONSE,
    EXISTING_DATASET_RESPONSE
)

def test_scan_username_dataset_folders(
        set_username_dataset_config, mock_scp_server, mock_key_pair,
        mock_staging_path):
    """Test ability to scan the Username / Dataset folder structure.
    """
    from mydata.conf import settings
    from mydata.tasks.folders import scan_folders
    from mydata.tasks.uploads import upload_folder
    from mydata.models.lookup import LookupStatus
    from mydata.models.upload import UploadMethod, UploadStatus
    from mydata.models.experiment import Experiment
    from mydata.models.dataset import Dataset

    # Firstly, let's test the case where we don't have an existing uploader
    # record, i.e. the GET query will return an empty list, so, we'll
    # need to create a new uploader record with POST:

    # Reset global settings' uploader instance, so we when we next call
    # the settings.uploader property method, we'll generate a
    # new Uploader instance, using the up-to-date
    # settings.general.instrument_name:
    settings.uploader = None
    with requests_mock.Mocker() as mocker:
        get_uploader_url = (
            "%s/api/v1/mydata_uploader/?format=json&uuid=00000000001"
        ) % settings.general.mytardis_url
        mocker.get(get_uploader_url, text=EMPTY_LIST_RESPONSE)
        get_facility_api_url = (
            "%s/api/v1/facility/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1"
            "&name=Test%%20Instrument"
        ) % settings.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)
        post_uploader_url = (
            "%s/api/v1/mydata_uploader/"
        ) % settings.general.mytardis_url
        mocker.post(post_uploader_url, text=MOCK_UPLOADER_RESPONSE)
        settings.uploader.upload_uploader_info()
    assert settings.uploader.name == "Test Instrument"

    # Now let's test the case where we have an existing uploader record:

    # Reset global settings' uploader instance, so we when we next call
    # the settings.uploader property method, we'll generate a
    # new Uploader instance, using the up-to-date
    # settings.general.instrument_name:
    settings.uploader = None
    with requests_mock.Mocker() as mocker:
        get_uploader_url = (
            "%s/api/v1/mydata_uploader/?format=json&uuid=00000000001"
        ) % settings.general.mytardis_url
        mocker.get(get_uploader_url, text=MOCK_EXISTING_UPLOADER_RESPONSE)
        get_facility_api_url = (
            "%s/api/v1/facility/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1"
            "&name=Test%%20Instrument"
        ) % settings.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)
        put_uploader_url = (
            "%s/api/v1/mydata_uploader/1/"
        ) % settings.general.mytardis_url
        mocker.put(put_uploader_url, text=MOCK_UPLOADER_RESPONSE)
        settings.uploader.upload_uploader_info()
    assert settings.uploader.name == "Test Instrument"

    settings.uploader.ssh_key_pair = mock_key_pair

    users = []
    folders = []

    def found_user(user):
        users.append(user)

    def found_dataset(folder):
        folders.append(folder)

        # Creating the experiment and dataset for the folder will be done
        # automatically when calling upload_folder, but for the mocked API
        # responses we want to provide in this test, it is easier to
        # explicitly create the experiment and dataset here:
        with requests_mock.Mocker() as mocker:
            get_exp_url = (
                "%s/api/v1/mydata_experiment/?format=json&title=%s"
                "&folder_structure=Username%%20/%%20Dataset&user_folder_name=%s"
            ) % (settings.general.mytardis_url, quote(folder.experiment_title),
                 quote(folder.user_folder_name))
            mocker.get(get_exp_url, text=EMPTY_LIST_RESPONSE)
            post_experiment_url = "%s/api/v1/mydata_experiment/" % settings.general.mytardis_url
            mocker.post(post_experiment_url, text=CREATED_EXP_RESPONSE)
            post_objectacl_url = "%s/api/v1/objectacl/" % settings.general.mytardis_url
            mocker.post(post_objectacl_url, status_code=201)
            get_dataset_url = (
                "%s/api/v1/dataset/?format=json&experiments__id=1"
                "&description=%s&instrument__id=1"
            ) % (settings.general.mytardis_url, quote(folder.name))
            mocker.get(get_dataset_url, text=EMPTY_LIST_RESPONSE)
            post_dataset_url = "%s/api/v1/dataset/" % settings.general.mytardis_url
            mock_dataset_response = CREATED_DATASET_RESPONSE.replace(
                "Created Dataset", folder.name)
            mocker.post(post_dataset_url, text=mock_dataset_response)
            folder.experiment = Experiment.get_or_create_exp_for_folder(folder)
            folder.dataset = Dataset.create_dataset_if_necessary(folder)

    found_exp = None
    found_group = None

    with requests_mock.Mocker() as mocker:
        get_user_api_url = (
            "%s/api/v1/user/?format=json&username=testfacility"
        ) % settings.general.mytardis_url
        mocker.get(get_user_api_url, text=MOCK_USER_RESPONSE)
        get_testuser1_url = (
            "%s/api/v1/user/?format=json&username=testuser1"
        ) % settings.general.mytardis_url
        mocker.get(get_testuser1_url, text=MOCK_TESTUSER1_RESPONSE)
        get_testuser2_url = get_testuser1_url.replace("testuser1", "testuser2")
        mocker.get(get_testuser2_url, text=MOCK_TESTUSER2_RESPONSE)
        get_invalid_user_url = (
            "%s/api/v1/user/?format=json&username=INVALID_USER"
        ) % settings.general.mytardis_url
        mocker.get(get_invalid_user_url, text=EMPTY_LIST_RESPONSE)
        get_facility_api_url = (
            "%s/api/v1/facility/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1"
            "&name=Test%%20Instrument"
        ) % settings.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)

        scan_folders(found_user, found_group, found_exp, found_dataset)

    assert sorted([user.username for user in users]) == ["INVALID_USER", "testuser1", "testuser2"]
    expected_folders = [
        "Birds", "Dataset with spaces", "Flowers", "InvalidUserDataset1"]
    assert sorted([folder.name for folder in folders]) == expected_folders
    assert sum([folder.num_files for folder in folders]) == 12

    with requests_mock.Mocker() as mocker:
        get_facility_api_url = "%s/api/v1/facility/?format=json" % settings.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1"
            "&name=Test%%20Instrument"
        ) % settings.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)
        get_exp_url_template = Template((
            "%s/api/v1/mydata_experiment/?format=json&title=Test%%20Instrument%%20-%%20$name"
            "&folder_structure=Username%%20/%%20Dataset&user_folder_name=$username"
        ) % settings.general.mytardis_url)
        for username, name in [
                ("testuser1", quote("Test User1")),
                ("testuser2", quote("Test User2")),
                ("INVALID_USER", "INVALID_USER%20%28USER%20NOT%20FOUND%20IN%20MYTARDIS%29")]:
            mocker.get(
                get_exp_url_template.substitute(username=username, name=name),
                text=EXISTING_EXP_RESPONSE.replace("Existing Experiment", name))
        verify_url = "%s/api/v1/dataset_file/1/verify/" % settings.general.mytardis_url
        mocker.get(verify_url)
        for folder in folders:
            get_dataset_url = (
                "%s/api/v1/dataset/?format=json&experiments__id=1"
                "&description=%s&instrument__id=1"
            ) % (settings.general.mytardis_url, quote(folder.name))
            mocker.get(get_dataset_url, text=EXISTING_DATASET_RESPONSE.replace("Existing Dataset", folder.name))

            get_df_url_template = Template((
                "%s/api/v1/mydata_dataset_file/?format=json&dataset__id=1&filename=$filename&directory="
            ) % settings.general.mytardis_url)

            for dfi in range(0, folder.num_files):
                datafile_path = folder.get_datafile_path(dfi)
                datafile_dir = folder.get_datafile_directory(dfi)
                datafile_name = os.path.basename(datafile_path)
                get_datafile_url = get_df_url_template.substitute(filename=quote(datafile_name))
                mocker.get(get_datafile_url, text=EMPTY_LIST_RESPONSE)
                post_datafile_url = "%s/api/v1/mydata_dataset_file/" % settings.general.mytardis_url
                temp_url = ""
                if folder.dataset:
                    if datafile_dir:
                        temp_url = "%s/DatasetDescription-%s/%s/%s" \
                            % (mock_staging_path, folder.dataset.id, datafile_dir, datafile_name)
                    else:
                        temp_url = "%s/DatasetDescription-%s/%s" \
                            % (mock_staging_path, folder.dataset.id, datafile_name)
                mocker.post(post_datafile_url, status_code=201, text=temp_url,
                            headers={"Location": "/api/v1/mydata_dataset_file/1/"})

        lookups = []
        uploads = []

        def lookup_callback(lookup):
            lookups.append(lookup)

        def upload_callback(upload):
            uploads.append(upload)

        get_uploader_url = (
            "%s/api/v1/mydata_uploader/?format=json&uuid=00000000001"
        ) % settings.general.mytardis_url
        mocker.get(get_uploader_url, text=MOCK_EXISTING_UPLOADER_RESPONSE)
        put_uploader_url = (
            "%s/api/v1/mydata_uploader/1/"
        ) % settings.general.mytardis_url
        mocker.put(put_uploader_url, text=MOCK_UPLOADER_RESPONSE)
        get_urr_url = (
            "%s/api/v1/mydata_uploaderregistrationrequest/?format=json"
            "&uploader__uuid=00000000001&requester_key_fingerprint=%s"
        ) % (settings.general.mytardis_url, settings.uploader.ssh_key_pair.fingerprint)
        _, scp_port = mock_scp_server.server_address
        mocker.get(get_urr_url, text=Template(MOCK_URR_RESPONSE).substitute(scp_port=scp_port))

        for folder in folders:
            upload_folder(folder, lookup_callback, upload_callback,
                          upload_method=UploadMethod.SCP)

        # Ensure that all 12 files were looked up:
        assert len(lookups) == 12

        for lookup in lookups:
            msg = "File: %s had unexpected lookup result: %s" % (lookup.filename, lookup.message)
            assert lookup.status == LookupStatus.NOT_FOUND, msg

        # Ensure that all 12 files were uploaded:
        assert len(uploads) == 12

        for upload in uploads:
            msg = "%s: %s" % (upload.filename, upload.message)
            assert upload.status == UploadStatus.COMPLETED, msg
