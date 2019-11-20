"""
Model class for the settings displayed in the settings dialog
and saved to disk in MyData.cfg
"""
# pylint: disable=import-outside-toplevel
# pylint: disable=bare-except
import os
import pickle
import traceback

from urllib.parse import urlparse

from ...constants import APPNAME
from ...logs import logger
from ...threads.locks import LOCKS
from ...utils import create_config_path_if_necessary
from .general import GeneralSettingsModel
from .filters import FiltersSettingsModel
from .advanced import AdvancedSettingsModel
from .miscellaneous import MiscellaneousSettingsModel
from .miscellaneous import LastSettingsUpdateTrigger


class SettingsModel():
    """
    Model class for the settings displayed in the settings dialog
    and saved to disk in MyData.cfg
    """
    def __init__(self, config_path):
        super(SettingsModel, self).__init__()

        # The location on disk of MyData.cfg
        # e.g. "C:\\ProgramData\\Monash University\\MyData\\MyData.cfg" or
        # "/Users/jsmith/Library/Application Support/MyData/MyData.cfg":
        self._config_path = config_path

        self._verified_datafiles_cache = dict()

        self._uploader = None

        self.last_settings_update_trigger = \
            LastSettingsUpdateTrigger.READ_FROM_DISK

        self.models = dict(
            general=GeneralSettingsModel(),
            filters=FiltersSettingsModel(),
            advanced=AdvancedSettingsModel(),
            miscellaneous=MiscellaneousSettingsModel())

        self.set_default_config()

    @property
    def general(self):
        """
        Settings in the Settings Dialog's General tab
        """
        return self.models['general']

    @property
    def filters(self):
        """
        Settings in the Settings Dialog's Filters tab
        """
        return self.models['filters']

    @property
    def advanced(self):
        """
        Settings in the Settings Dialog's Advanced tab
        """
        return self.models['advanced']

    @property
    def miscellaneous(self):
        """
        Miscellaneous settings
        """
        return self.models['miscellaneous']

    def __setitem__(self, key, item):
        """
        Set a config item by field name.
        """
        if key in self.general.fields:
            self.general.mydata_config[key] = item
        elif key in self.filters.fields:
            self.filters.mydata_config[key] = item
        elif key in self.advanced.fields:
            self.advanced.mydata_config[key] = item
        elif key in self.miscellaneous.fields:
            self.miscellaneous.mydata_config[key] = item
        else:
            raise KeyError(key)

    def __getitem__(self, key):
        """
        Get a config item by field name.
        """
        if key in self.general.fields:
            return self.general.mydata_config[key]
        if key in self.filters.fields:
            return self.filters.mydata_config[key]
        if key in self.advanced.fields:
            return self.advanced.mydata_config[key]
        if key in self.miscellaneous.fields:
            return self.miscellaneous.mydata_config[key]
        raise KeyError(key)

    @property
    def uploader(self):
        """
        Get the uploader (MyData instance) model

        This could be called from multiple threads
        simultaneously, so it requires locking.
        """
        from ..uploader import Uploader
        if self._uploader:
            return self._uploader
        try:
            LOCKS.create_uploader.acquire()  # pylint: disable=no-member
            self._uploader = Uploader()
            return self._uploader
        finally:
            LOCKS.create_uploader.release()  # pylint: disable=no-member

    @uploader.setter
    def uploader(self, uploader):
        """
        Set uploader model (representing this MyData instance)
        """
        self._uploader = uploader

    def required_field_is_blank(self):
        """
        Return True if a required field is blank
        """
        return self.general.instrument_name == "" or \
            self.general.facility_name == "" or \
            self.general.contact_name == "" or \
            self.general.contact_email == "" or \
            self.general.data_directory == "" or \
            self.general.mytardis_url == "" or \
            self.general.username == "" or \
            self.general.api_key == ""

    def set_default_config(self):
        """
        Set default values for configuration parameters
        that will appear in MyData.cfg
        """
        self.general.set_defaults()
        self.filters.set_defaults()
        self.advanced.set_defaults()
        self.miscellaneous.set_defaults()

    @property
    def default_headers(self):
        """
        Default HTTP headers, providing authorization for MyTardis API.
        """
        return {
            "Authorization": "ApiKey %s:%s" % (self.general.username,
                                               self.general.api_key),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @property
    def verified_datafiles_cache(self):
        """
        We use a serialized dictionary to cache DataFile lookup results.
        We'll use a separate cache file for each MyTardis server we connect to.
        """
        parsed = urlparse(self.general.mytardis_url)
        return os.path.join(
            os.path.dirname(self.config_path),
            "verified-files-%s-%s.pkl" %
            (parsed.scheme, parsed.netloc))

    def initialize_verified_datafiles_cache(self):
        """
        We use a serialized dictionary to cache DataFile lookup results.
        We'll use a separate cache file for each MyTardis server we connect to.
        """
        try:
            if os.path.exists(self._verified_datafiles_cache):
                with open(self._verified_datafiles_cache, 'rb') as cache_file:
                    self._verified_datafiles_cache = pickle.load(cache_file)
            else:
                self._verified_datafiles_cache = dict()
        except:
            self._verified_datafiles_cache = dict()
            logger.warning(traceback.format_exc())

    def save_verified_datafiles_cache(self):
        """
        We use a serialized dictionary to cache DataFile lookup results.
        We'll use a separate cache file for each MyTardis server we connect to.
        """
        with LOCKS.close_cache:  # pylint: disable=no-member
            try:
                with open(self._verified_datafiles_cache,
                          'wb') as cache_file:
                    pickle.dump(self._verified_datafiles_cache, cache_file)
            except:
                logger.warning("Couldn't save verified datafiles cache.")
                logger.warning(traceback.format_exc())

    @property
    def config_path(self):
        """
        The location on disk of MyData.cfg
        e.g. "C:\\ProgramData\\Monash University\\MyData\\MyData.cfg" or
        "/Users/jsmith/Library/Application Support/MyData/MyData.cfg"
        """
        if not self._config_path:
            appdir_path = create_config_path_if_necessary()
            self._config_path = os.path.join(appdir_path, APPNAME + '.cfg')
        return self._config_path

    @config_path.setter
    def config_path(self, config_path):
        """
        The location on disk of MyData.cfg
        e.g. "C:\\ProgramData\\Monash University\\MyData\\MyData.cfg" or
        "/Users/jsmith/Library/Application Support/MyData/MyData.cfg"
        """
        self._config_path = config_path
