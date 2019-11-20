"""
Test ability to handle instrument-related exceptions.
"""
import requests_mock
import pytest

from requests.exceptions import HTTPError

from tests.fixtures import set_exp_dataset_config
from tests.mocks import (
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE,
    EMPTY_LIST_RESPONSE
)


def test_instrument_exceptions(set_exp_dataset_config):
    """Test ability to handle instrument-related exceptions.
    """
    from mydata.conf import settings
    from mydata.models.instrument import Instrument

    with requests_mock.Mocker() as mocker:
        get_facility_url = (
            "%s/api/v1/facility/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_facility_url, text=MOCK_FACILITY_RESPONSE)
        facility = settings.general.facility
        assert facility

    api_key = settings.general.api_key
    settings.general.api_key = "invalid"
    with requests_mock.Mocker() as mocker:
        get_instrument_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1"
            "&name=Unauthorized%%20Instrument"
        ) % settings.general.mytardis_url
        mocker.get(get_instrument_url, status_code=401)
        with pytest.raises(HTTPError) as excinfo:
            _ = Instrument.get_instrument(facility, "Unauthorized Instrument")
        assert excinfo.value.response.status_code == 401

    with requests_mock.Mocker() as mocker:
        post_instrument_url = "%s/api/v1/instrument/" % settings.general.mytardis_url
        mocker.post(post_instrument_url, status_code=401)
        with pytest.raises(HTTPError) as excinfo:
            _ = Instrument.create_instrument(facility, "Unauthorized Instrument")
        assert excinfo.value.response.status_code == 401

    settings.general.api_key = api_key

    with requests_mock.Mocker() as mocker:
        post_instrument_url = "%s/api/v1/instrument/" % settings.general.mytardis_url
        mocker.post(post_instrument_url, status_code=500)
        with pytest.raises(HTTPError) as excinfo:
            _ = Instrument.create_instrument(facility, "Instrument name")
        assert excinfo.value.response.status_code == 500

    with requests_mock.Mocker() as mocker:
        get_facility_url = (
            "%s/api/v1/facility/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_facility_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_url = (
            "%s/api/v1/instrument/?format=json"
            "&facility__id=1&name=Test%%20Instrument"
        ) % settings.general.mytardis_url
        mocker.get(get_instrument_url, text=MOCK_INSTRUMENT_RESPONSE)
        instrument = settings.general.instrument

    with requests_mock.Mocker() as mocker:
        put_instrument_url = "%s/api/v1/instrument/1/" % settings.general.mytardis_url
        mocker.put(put_instrument_url, status_code=500)
        with pytest.raises(HTTPError) as excinfo:
            instrument.rename("New instrument name")
        assert excinfo.value.response.status_code == 500

    with requests_mock.Mocker() as mocker:
        get_facility_url = (
            "%s/api/v1/facility/?format=json"
        ) % settings.general.mytardis_url
        mocker.get(get_facility_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_url = (
            "%s/api/v1/instrument/?format=json"
            "&facility__id=1&name=Test%%20Instrument"
        ) % settings.general.mytardis_url
        mocker.get(get_instrument_url, text=MOCK_INSTRUMENT_RESPONSE)
        new_instrument_get_url = (
            "%s/api/v1/instrument/?format=json"
            "&facility__id=1&name=New%%20instrument%%20name"
        ) % settings.general.mytardis_url
        mocker.get(new_instrument_get_url, text=EMPTY_LIST_RESPONSE)
        put_instrument_url = "%s/api/v1/instrument/1/" % settings.general.mytardis_url
        mocker.put(put_instrument_url, status_code=500)
        with pytest.raises(HTTPError) as excinfo:
            instrument.rename_instrument(
                settings.general.facility_name,
                settings.general.instrument_name,
                "New instrument name")
        assert excinfo.value.response.status_code == 500
