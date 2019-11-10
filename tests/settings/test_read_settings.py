"""
test_read_settings.py

Tests for reading MyData settings from a MyData.cfg file
"""
import importlib
import os

import pytest

from mydata.models.settings.validation import validate_settings
from mydata.utils.exceptions import InvalidSettings


@pytest.fixture
def set_mydata_config_path():
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-username-dataset.cfg'))


def test_read_settings(set_mydata_config_path):
    from mydata import settings
    settings = importlib.reload(settings)
    SETTINGS = settings.SETTINGS
    assert SETTINGS.config_path == os.environ['MYDATA_CONFIG_PATH']
    assert SETTINGS.general.instrument_name == 'Test Instrument'
    assert SETTINGS.general.mytardis_url == 'http://127.0.0.1:9000'

    with pytest.raises(InvalidSettings) as excinfo:
        validate_settings()
    assert excinfo.type == InvalidSettings
    assert "MyTardis URL" in str(excinfo.value)
