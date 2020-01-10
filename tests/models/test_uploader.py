"""
Test ability to create an Uploader and an Uploader Registration Request
"""
import pytest
import requests_mock

from tests.fixtures import set_username_dataset_config, mock_key_pair

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
    EXISTING_EXP_RESPONSE,
    EXISTING_DATASET_RESPONSE,
    CREATED_URR_RESPONSE,
    MOCK_URR_MISSING_SBOX_ATTRS,
)


def test_uploader(set_username_dataset_config, mock_key_pair):
    """Test ability to create an Uploader and an Uploader Registration Request
    """
    from mydata.conf import settings
    from mydata.utils.exceptions import (
        NoApprovedStorageBox,
        StorageBoxAttributeNotFound,
        StorageBoxOptionNotFound,
    )

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

    # Now let's test requesting staging access when we don't have an
    # existing UploaderRegistrationRequest:
    with requests_mock.Mocker() as mocker:
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
        mocker.get(get_urr_url, text=EMPTY_LIST_RESPONSE)
        post_urr_url = (
            "%s/api/v1/mydata_uploaderregistrationrequest/"
        ) % settings.general.mytardis_url
        mocker.post(post_urr_url, text=CREATED_URR_RESPONSE)

        settings.uploader.request_staging_access()

        urr = settings.uploader.upload_to_staging_request
        assert not urr.approved
        assert not urr.approved_storage_box

        with pytest.raises(NoApprovedStorageBox):
            _ = urr.scp_hostname

        with pytest.raises(NoApprovedStorageBox):
            _ = urr.scp_username

        with pytest.raises(NoApprovedStorageBox):
            _ = urr.scp_port

        with pytest.raises(NoApprovedStorageBox):
            _ = urr.location

    # Now let's test requesting staging access when we have an
    # existing UploaderRegistrationRequest:
    with requests_mock.Mocker() as mocker:
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
        mocker.get(get_urr_url, text=MOCK_URR_MISSING_SBOX_ATTRS)

        settings.uploader.request_staging_access()

        urr = settings.uploader.upload_to_staging_request
        assert urr.approved
        assert urr.approved_storage_box

        with pytest.raises(StorageBoxAttributeNotFound):
            _ = urr.scp_hostname

        with pytest.raises(StorageBoxAttributeNotFound):
            _ = urr.scp_username

        # If the scp_port storage box attribute is missing, it defaults to 22:
        assert urr.scp_port == "22"

        with pytest.raises(StorageBoxOptionNotFound):
            _ = urr.location
