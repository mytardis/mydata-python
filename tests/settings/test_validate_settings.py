"""
Test ability to validate settings.
"""
import re

import pytest
import requests_mock

from tests.mocks import (
    mock_testfacility_user_response,
    MOCK_API_ENDPOINTS_RESPONSE,
    mock_test_facility_response,
    mock_test_instrument_response,
)

from tests.fixtures import set_exp_dataset_config


def test_validate_settings(set_exp_dataset_config):
    """Test ability to validate settings.
    """
    from mydata.conf import settings
    from mydata.models.settings.validation import validate_settings
    from mydata.utils.exceptions import InvalidSettings

    with requests_mock.Mocker() as mocker:
        list_api_endpoints_url = (
            "%s/api/v1/?format=json" % settings.general.mytardis_url
        )
        mocker.get(list_api_endpoints_url, text=MOCK_API_ENDPOINTS_RESPONSE)
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        validate_settings()

        old_value = settings.general.mytardis_url
        settings.general.mytardis_url = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid MyTardis URL" in str(excinfo.value)
        settings.general.mytardis_url = old_value

        old_value = settings.general.data_directory
        settings.general.data_directory = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid data directory" in str(excinfo.value)
        settings.general.data_directory = old_value

        old_value = settings.general.data_directory
        settings.general.data_directory = "this/folder/does/not/exist"
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "doesn't exist" in str(excinfo.value)
        settings.general.data_directory = old_value

        old_value = settings.general.instrument_name
        old_value = settings.general.instrument_name
        settings.general.instrument_name = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid instrument name" in str(excinfo.value)
        settings.general.instrument_name = old_value

        old_value = settings.general.facility_name
        settings.general.facility_name = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid facility name" in str(excinfo.value)
        settings.general.facility_name = old_value

        old_value = settings.general.facility_name
        settings.general.facility_name = "Invalid"
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert 'Facility "Invalid" was not found in MyTardis.' in str(excinfo.value)
        settings.general.facility_name = old_value

        old_value = settings.general.contact_name
        settings.general.contact_name = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid contact name" in str(excinfo.value)
        settings.general.contact_name = old_value

        old_value = settings.general.contact_email
        settings.general.contact_email = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid contact email" in str(excinfo.value)
        settings.general.contact_email = old_value

        old_value = settings.general.contact_email
        settings.general.contact_email = "invalid-email-address"
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a valid contact email" in str(excinfo.value)
        settings.general.contact_email = old_value

        old_value = settings.advanced.folder_structure
        old_value2 = settings.advanced.validate_folder_structure
        settings.advanced.folder_structure = "Email / Dataset"
        settings.advanced.validate_folder_structure = True
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert re.match(
            "Folder name .* is not a valid email address.", str(excinfo.value)
        )
        settings.advanced.folder_structure = old_value
        settings.advanced.validate_folder_structure = old_value2

        old_value = settings.general.username
        settings.general.username = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter a MyTardis username" in str(excinfo.value)
        settings.general.username = old_value

        old_value = settings.general.api_key
        settings.general.api_key = ""
        with pytest.raises(InvalidSettings) as excinfo:
            validate_settings()
        assert "Please enter your MyTardis API key" in str(excinfo.value)
        settings.general.api_key = old_value
