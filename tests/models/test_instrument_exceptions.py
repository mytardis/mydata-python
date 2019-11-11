"""
Test ability to handle instrument-related exceptions.
"""
import importlib
import json
import os

import requests_mock
import pytest

from requests.exceptions import HTTPError


@pytest.fixture
def set_mydata_config_path():
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-exp-dataset.cfg'))


def test_instrument_exceptions(set_mydata_config_path):
    """Test ability to handle instrument-related exceptions.
    """
    from mydata import settings
    settings = importlib.reload(settings)
    from mydata.models.instrument import Instrument
    SETTINGS = settings.SETTINGS  # pylint: disable=invalid-name

    mock_facility_response = json.dumps({
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 1
        },
        "objects": [{
            "id": 1,
            "name": "Test Facility",
            "manager_group": {
                "id": 1,
                "name": "test-facility-managers"
            },
            "resource_uri": "/api/v1/facility/1/"
        }]
    })
    with requests_mock.Mocker() as mocker:
        get_facility_url = (
            "%s/api/v1/facility/?format=json"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_facility_url, text=mock_facility_response)
        facility = SETTINGS.general.facility
        assert facility

    api_key = SETTINGS.general.api_key
    SETTINGS.general.api_key = "invalid"
    with requests_mock.Mocker() as mocker:
        get_instrument_url = (
            "%s/api/v1/instrument/?format=json&facility__id=1"
            "&name=Unauthorized%%20Instrument"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_instrument_url, status_code=401)
        with pytest.raises(HTTPError) as excinfo:
            _ = Instrument.get_instrument(facility, "Unauthorized Instrument")
        assert excinfo.value.response.status_code == 401

    with requests_mock.Mocker() as mocker:
        post_instrument_url = "%s/api/v1/instrument/" % SETTINGS.general.mytardis_url
        mocker.post(post_instrument_url, status_code=401)
        with pytest.raises(HTTPError) as excinfo:
            _ = Instrument.create_instrument(facility, "Unauthorized Instrument")
        assert excinfo.value.response.status_code == 401

    SETTINGS.general.api_key = api_key

    with requests_mock.Mocker() as mocker:
        post_instrument_url = "%s/api/v1/instrument/" % SETTINGS.general.mytardis_url
        mocker.post(post_instrument_url, status_code=500)
        with pytest.raises(HTTPError) as excinfo:
            _ = Instrument.create_instrument(facility, "Instrument name")
        assert excinfo.value.response.status_code == 500

    mock_instrument_response = json.dumps({
        "meta": {
            "limit": 20,
            "next": None,
            "offset": 0,
            "previous": None,
            "total_count": 1
        },
        "objects": [{
            "id": 1,
            "name": "Test Instrument",
            "facility": {
                "id": 1,
                "name": "Test Facility",
                "manager_group": {
                    "id": 1,
                    "name": "test-facility-managers"
                }
            }
        }]
    })
    with requests_mock.Mocker() as mocker:
        get_facility_url = (
            "%s/api/v1/facility/?format=json"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_facility_url, text=mock_facility_response)
        get_instrument_url = (
            "%s/api/v1/instrument/?format=json"
            "&facility__id=1&name=Test%%20Instrument"
        ) % SETTINGS.general.mytardis_url
        mocker.get(get_instrument_url, text=mock_instrument_response)
        instrument = SETTINGS.general.instrument

    with requests_mock.Mocker() as mocker:
        put_instrument_url = "%s/api/v1/instrument/1/" % SETTINGS.general.mytardis_url
        mocker.put(put_instrument_url, status_code=500)
        with pytest.raises(HTTPError) as excinfo:
            instrument.rename("New instrument name")
        assert excinfo.value.response.status_code == 500
