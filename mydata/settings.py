"""
The global SettingsModel instance.

If the MYDATA_CONFIG_PATH environment variable is not set,
MyData will determine an appropriate location for settings
using the Python appdirs library.
"""
import os

from mydata.models.settings import SettingsModel

SETTINGS = SettingsModel(configPath=os.environ.get('MYDATA_CONFIG_PATH'))
