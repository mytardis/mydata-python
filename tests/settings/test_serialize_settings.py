"""
test_serialize_settings.py

Tests for writing/reading MyData settings to/from a MyData.cfg file
"""
import os
import tempfile

import pytest

from tests.fixtures import set_exp_dataset_config


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
