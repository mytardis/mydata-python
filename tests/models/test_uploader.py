"""
Test ability to create an Uploader and an Uploader Registration Request
"""
import pytest
import requests_mock

from tests.fixtures import (
    set_username_dataset_config,
    mock_key_pair
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
    EXISTING_EXP_RESPONSE,
    EXISTING_DATASET_RESPONSE,
    CREATED_URR_RESPONSE,
    MOCK_URR_MISSING_SBOX_ATTRS
)

def test_uploader(
        set_username_dataset_config, mock_key_pair):
    """Test ability to create an Uploader and an Uploader Registration Request
    """
    from mydata.settings import SETTINGS
    from mydata.utils.exceptions import (
        NoApprovedStorageBox,
        StorageBoxAttributeNotFound,
        StorageBoxOptionNotFound
    )

    # Firstly, let's test the case where we don't have an existing uploader
    # record, i.e. the GET query will return an empty list, so, we'll
    # need to create a new uploader record with POST:

    # Reset global settings' uploader instance, so we when we next call
    # the SETTINGS.uploader property method, we'll generate a
    # new Uploader instance, using the up-to-date
    # SETTINGS.general.instrument_name:
    SETTINGS.uploader = None
    with requests_mock.Mocker() as mocker:
        get_uploader_url = (
            "%s/api/v1/mydata_uploader/?format=json&uuid=00000000001"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_uploader_url, text=EMPTY_LIST_RESPONSE)
        get_facility_api_url = (
            "%s/api/v1/facility/?format=json"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1"
            "&name=Test%%20Instrument"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)
        post_uploader_url = (
            "%s/api/v1/mydata_uploader/"
        ) % SETTINGS.general.mytardis_url
        mocker.post(post_uploader_url, text=MOCK_UPLOADER_RESPONSE)
        SETTINGS.uploader.upload_uploader_info()
    assert SETTINGS.uploader.name == "Test Instrument"

    # Now let's test the case where we have an existing uploader record:

    # Reset global settings' uploader instance, so we when we next call
    # the SETTINGS.uploader property method, we'll generate a
    # new Uploader instance, using the up-to-date
    # SETTINGS.general.instrument_name:
    SETTINGS.uploader = None
    with requests_mock.Mocker() as mocker:
        get_uploader_url = (
            "%s/api/v1/mydata_uploader/?format=json&uuid=00000000001"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_uploader_url, text=MOCK_EXISTING_UPLOADER_RESPONSE)
        get_facility_api_url = (
            "%s/api/v1/facility/?format=json"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1"
            "&name=Test%%20Instrument"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)
        put_uploader_url = (
            "%s/api/v1/mydata_uploader/1/"
        ) % SETTINGS.general.mytardis_url
        mocker.put(put_uploader_url, text=MOCK_UPLOADER_RESPONSE)
        SETTINGS.uploader.upload_uploader_info()
    assert SETTINGS.uploader.name == "Test Instrument"

    SETTINGS.uploader.ssh_key_pair = mock_key_pair

    # Now let's test requesting staging access when we don't have an
    # existing UploaderRegistrationRequest:
    with requests_mock.Mocker() as mocker:
        get_uploader_url = (
            "%s/api/v1/mydata_uploader/?format=json&uuid=00000000001"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_uploader_url, text=MOCK_EXISTING_UPLOADER_RESPONSE)
        put_uploader_url = (
            "%s/api/v1/mydata_uploader/1/"
        ) % SETTINGS.general.mytardis_url
        mocker.put(put_uploader_url, text=MOCK_UPLOADER_RESPONSE)
        get_urr_url = (
            "%s/api/v1/mydata_uploaderregistrationrequest/?format=json"
            "&uploader__uuid=00000000001&requester_key_fingerprint=%s"
        ) % (SETTINGS.general.mytardis_url, SETTINGS.uploader.ssh_key_pair.fingerprint)
        mocker.get(get_urr_url, text=EMPTY_LIST_RESPONSE)
        post_urr_url = (
            "%s/api/v1/mydata_uploaderregistrationrequest/"
        ) % SETTINGS.general.mytardis_url
        mocker.post(post_urr_url, text=CREATED_URR_RESPONSE)

        SETTINGS.uploader.request_staging_access()

        urr = SETTINGS.uploader.upload_to_staging_request
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
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_uploader_url, text=MOCK_EXISTING_UPLOADER_RESPONSE)
        put_uploader_url = (
            "%s/api/v1/mydata_uploader/1/"
        ) % SETTINGS.general.mytardis_url
        mocker.put(put_uploader_url, text=MOCK_UPLOADER_RESPONSE)
        get_urr_url = (
            "%s/api/v1/mydata_uploaderregistrationrequest/?format=json"
            "&uploader__uuid=00000000001&requester_key_fingerprint=%s"
        ) % (SETTINGS.general.mytardis_url, SETTINGS.uploader.ssh_key_pair.fingerprint)
        mocker.get(get_urr_url, text=MOCK_URR_MISSING_SBOX_ATTRS)

        SETTINGS.uploader.request_staging_access()

        urr = SETTINGS.uploader.upload_to_staging_request
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
