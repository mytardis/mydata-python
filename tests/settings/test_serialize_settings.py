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
    from mydata.settings import SETTINGS
    from mydata.models.settings.validation import validate_settings
    from mydata.utils.exceptions import InvalidSettings

    assert SETTINGS.config_path == os.environ['MYDATA_CONFIG_PATH']
    assert SETTINGS.general.instrument_name == 'Test Instrument'
    assert SETTINGS.general.mytardis_url == 'http://127.0.0.1:9000'

    # Validate settings, and expect MyTardis URL to raise InvalidSettings:
    with pytest.raises(InvalidSettings) as excinfo:
        validate_settings()
    assert "MyTardis URL" in str(excinfo.value)


def test_write_settings(set_exp_dataset_config):
    """Test writing settings to disk
    """
    from mydata.models.settings.serialize import (
        save_settings_to_disk, load_settings)
    from mydata.settings import SETTINGS

    SETTINGS.general.contact_name = "Joe Bloggs"
    SETTINGS.general.contact_email = "Joe.Bloggs@example.com"

    with tempfile.NamedTemporaryFile() as temp_file:
        temp_config_path = temp_file.name

    save_settings_to_disk(temp_config_path)

    SETTINGS.general.contact_name = "Modified Name"
    SETTINGS.general.contact_email = "Modified.Name@example.com"

    load_settings(SETTINGS, temp_config_path)

    assert SETTINGS.general.contact_name == "Joe Bloggs"
    assert SETTINGS.general.contact_email == "Joe.Bloggs@example.com"
