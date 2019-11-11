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
    assert SETTINGS.config_path == os.environ['MYDATA_CONFIG_PATH']
    from mydata.models.settings.validation import validate_settings

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
