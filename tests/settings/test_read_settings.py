"""
test_read_settings.py

Tests for reading MyData settings from a MyData.cfg file
"""
import os

import pytest

from tests.fixtures import set_exp_dataset_config


def test_read_settings(set_exp_dataset_config):
    from mydata.settings import SETTINGS
    from mydata.models.settings.validation import validate_settings
    from mydata.utils.exceptions import InvalidSettings

    assert SETTINGS.config_path == os.environ['MYDATA_CONFIG_PATH']
    assert SETTINGS.general.instrument_name == 'Test Instrument'
    assert SETTINGS.general.mytardis_url == 'http://127.0.0.1:9000'

    with pytest.raises(InvalidSettings) as excinfo:
        validate_settings()
    assert excinfo.type == InvalidSettings
    assert "MyTardis URL" in str(excinfo.value)
