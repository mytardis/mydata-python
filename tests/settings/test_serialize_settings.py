"""
test_serialize_settings.py

Tests for writing/reading MyData settings to/from a MyData.cfg file
"""
import datetime
import os
import sys
import tempfile

from string import Template

import pytest
import requests_mock

from tests.mocks import MOCK_UPLOADER_WITH_SETTINGS

from tests.fixtures import set_exp_dataset_config
from tests.utils import unload_modules


def test_read_settings(set_exp_dataset_config):
    """Test reading settings from tests/testdata/testdata-exp-dataset.cfg

    Check some settings which are known to exist in
    tests/testdata/testdata-exp-dataset.cfg
    """
    from mydata.conf import settings
    from mydata.models.settings.validation import validate_settings
    from mydata.utils.exceptions import InvalidSettings

    assert settings.config_path == os.environ["MYDATA_CONFIG_PATH"]
    assert settings.general.instrument_name == "Test Instrument"
    assert settings.general.mytardis_url == "https://mytardis.example.com"

    # Validate settings, and expect MyTardis URL to raise InvalidSettings:
    with pytest.raises(InvalidSettings) as excinfo:
        validate_settings()
    assert "MyTardis URL" in str(excinfo.value)


def test_write_settings(set_exp_dataset_config):
    """Test writing settings to disk
    """
    from mydata.models.settings.serialize import save_settings_to_disk, load_settings
    from mydata.conf import settings

    settings.general.contact_name = "Joe Bloggs"
    settings.general.contact_email = "Joe.Bloggs@example.com"

    with tempfile.NamedTemporaryFile() as temp_file:
        temp_config_path = temp_file.name

    save_settings_to_disk(temp_config_path)

    settings.general.contact_name = "Modified Name"
    settings.general.contact_email = "Modified.Name@example.com"

    settings.uploader = None

    load_settings(temp_config_path)

    assert settings.general.contact_name == "Joe Bloggs"
    assert settings.general.contact_email == "Joe.Bloggs@example.com"


def test_check_for_updated_settings_on_server():
    """Test checking for updated settings on server
    """
    # Don't use a fixture to load the settings, because we want to mock
    # the URLs used to check for updating settings on the server before
    # loading settings:
    unload_modules()
    assert "mydata.settings" not in sys.modules
    os.environ["MYDATA_CONFIG_PATH"] = os.path.abspath(
        os.path.join(".", "tests", "testdata", "testdata-exp-dataset.cfg")
    )

    with requests_mock.Mocker() as mocker:
        get_uploader_url = (
            "https://mytardis.example.com/api/v1/mydata_uploader/?format=json"
            "&uuid=1234567890"
        )
        uploader_response = Template(MOCK_UPLOADER_WITH_SETTINGS).substitute(
            settings_updated=str(datetime.datetime.now())
        )
        mocker.get(get_uploader_url, text=uploader_response)
        from mydata.conf import settings

        # Test updating some string setting values from the server:
        assert settings.general.instrument_name == "Updated Instrument Name"
        assert settings.general.facility_name == "Updated Facility Name"
        assert settings.general.contact_name == "Updated Contact Name"
        assert settings.general.contact_email == "Updated.Contact.Email@example.com"

        # Test updating a boolean setting value from the server:
        assert not settings.filters.ignore_new_files

        # Test updating a floating-point setting value from the server:
        assert settings.miscellaneous.verification_delay == 4.0

        # An invalid setting value (not a floating point number) is specified
        # for connection_timeout in MOCK_UPLOADER_WITH_SETTINGS:
        assert (
            settings.miscellaneous.connection_timeout
            == settings.miscellaneous.default["connection_timeout"]
        )

    unload_modules()
