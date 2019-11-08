"""
test_read_settings.py

Tests for reading MyData settings from a MyData.cfg file
"""
import os

import pytest


@pytest.fixture
def set_mydata_config_path():
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-username-dataset.cfg'))

def test_read_settings(set_mydata_config_path):
    from mydata.models.settings.validation import ValidateSettings
    from mydata.utils.exceptions import InvalidSettings

    from mydata.settings import SETTINGS
    assert SETTINGS.general.instrumentName == 'Test Instrument'
    assert SETTINGS.general.myTardisUrl == 'http://127.0.0.1:9000'

    with pytest.raises(InvalidSettings) as excinfo:
        ValidateSettings()
    assert excinfo.type == InvalidSettings
    assert "MyTardis URL" in str(excinfo.value)
