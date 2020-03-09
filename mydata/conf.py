"""
The global Settings instance.

If the MYDATA_CONFIG_PATH environment variable is not set,
MyData will determine an appropriate location for settings
using the Python appdirs library.
"""
# pylint: disable=invalid-name
import os

from mydata.models.settings import Settings
from mydata.models.settings.serialize import load_settings
from mydata.utils.queues import init_lookup_threads

settings = Settings(config_path=os.environ.get("MYDATA_CONFIG_PATH"))
load_settings()
if settings.advanced.max_lookup_threads > 1:
    init_lookup_threads()
