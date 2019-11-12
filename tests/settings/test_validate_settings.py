"""
Test ability to validate settings.
"""
import os
import sys

import pytest
import requests_mock

from mydata.threads.flags import FLAGS

from tests.mocks import (
    MOCK_API_ENDPOINTS_RESPONSE,
    MOCK_USER_RESPONSE,
    MOCK_FACILITY_RESPONSE,
    MOCK_INSTRUMENT_RESPONSE
)

from tests.fixtures import set_exp_dataset_config
from tests.utils import unload_modules


def test_validate_settings(set_exp_dataset_config):
    """Test ability to validate settings.
    """
    from mydata.settings import SETTINGS
    from mydata.models.settings.validation import validate_settings
    from mydata.utils.exceptions import InvalidSettings

    with requests_mock.Mocker() as mocker:
        list_api_endpoints_url = "%s/api/v1/?format=json" % SETTINGS.general.mytardis_url
        mocker.get(list_api_endpoints_url, text=MOCK_API_ENDPOINTS_RESPONSE)
        get_user_api_url = "%s/api/v1/user/?format=json&username=testfacility" % SETTINGS.general.mytardis_url
        mocker.get(get_user_api_url, text=MOCK_USER_RESPONSE)
        get_facility_api_url = "%s/api/v1/facility/?format=json" % SETTINGS.general.mytardis_url
        mocker.get(get_facility_api_url, text=MOCK_FACILITY_RESPONSE)
        get_instrument_api_url = "%s/api/v1/instrument/?format=json&facility__id=1&name=Test%%20Instrument" % SETTINGS.general.mytardis_url
        mocker.get(get_instrument_api_url, text=MOCK_INSTRUMENT_RESPONSE)

        validate_settings()

        old_value = SETTINGS.general.mytardis_url
        SETTINGS.general.mytardis_url = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid MyTardis URL" in str(excinfo.value)
        SETTINGS.general.mytardis_url = old_value

        old_value = SETTINGS.general.data_directory
        SETTINGS.general.data_directory = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid data directory" in str(excinfo.value)
        SETTINGS.general.data_directory = old_value

        old_value = SETTINGS.general.instrument_name
        SETTINGS.general.instrument_name = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid instrument name" in str(excinfo.value)
        SETTINGS.general.instrument_name = old_value

        old_value = SETTINGS.general.facility_name
        SETTINGS.general.facility_name = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid facility name" in str(excinfo.value)
        SETTINGS.general.facility_name = old_value

        old_value = SETTINGS.general.contact_name
        SETTINGS.general.contact_name = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid contact name" in str(excinfo.value)
        SETTINGS.general.contact_name = old_value

        old_value = SETTINGS.general.contact_email
        SETTINGS.general.contact_email = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid contact email" in str(excinfo.value)
        SETTINGS.general.contact_email = old_value

        old_value = SETTINGS.general.username
        SETTINGS.general.username = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a MyTardis username" in str(excinfo.value)
        SETTINGS.general.username = old_value

        old_value = SETTINGS.general.api_key
        SETTINGS.general.api_key = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter your MyTardis API key" in str(excinfo.value)
        SETTINGS.general.api_key = old_value
