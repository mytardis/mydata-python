"""
Model class for the settings displayed in the General tab
of the settings dialog and saved to disk in MyData.cfg
"""
# pylint: disable=import-outside-toplevel
from .base import BaseSettings
from ...logs import logger


class GeneralSettings(BaseSettings):
    """
    Model class for the settings displayed in the General tab
    of the settings dialog and saved to disk in MyData.cfg
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        super().__init__()

        # Saved in MyData.cfg:
        self.mydata_config = dict()

        self.fields = [
            "instrument_name",
            "facility_name",
            "contact_name",
            "contact_email",
            "data_directory",
            "mytardis_url",
            "username",
            "api_key",
        ]

        self.default = dict(
            instrument_name="",
            facility_name="",
            contact_name="",
            contact_email="",
            data_directory="",
            mytardis_url="",
            username="",
            api_key="",
        )

        self._default_owner = None
        self._instrument = None
        self._facility = None

    @property
    def instrument_name(self):
        """
        Get instrument name
        """
        return self.mydata_config["instrument_name"]

    @instrument_name.setter
    def instrument_name(self, instrument_name):
        """
        Set instrument name
        """
        self.mydata_config["instrument_name"] = instrument_name
        self._instrument = None

    @property
    def instrument(self):
        """
        Return the Instrument for the specified instrument name
        """
        from ..instrument import Instrument

        if self._instrument:
            return self._instrument
        self._instrument = Instrument.get_instrument(
            self.facility, self.instrument_name
        )
        if not self._instrument:
            logger.info(
                'No instrument record with name "%s" was found '
                'in facility "%s", so we will create one.'
                % (self.instrument_name, self.facility_name)
            )
            self._instrument = Instrument.create_instrument(
                self.facility, self.instrument_name
            )
        return self._instrument

    @property
    def facility_name(self):
        """
        Get facility name
        """
        return self.mydata_config["facility_name"]

    @facility_name.setter
    def facility_name(self, facility_name):
        """
        Set facility name
        """
        self.mydata_config["facility_name"] = facility_name
        self._facility = None

    @property
    def facility(self):
        """
        Return the Facility for the specified facility name
        """
        from ..facility import Facility

        if self._facility:
            return self._facility
        facilities = Facility.get_my_facilities()
        for facility in facilities:
            if self.facility_name == facility.name:
                self._facility = facility
        return self._facility

    @property
    def contact_name(self):
        """
        Get contact name
        """
        return self.mydata_config["contact_name"]

    @contact_name.setter
    def contact_name(self, contact_name):
        """
        Set contact name
        """
        self.mydata_config["contact_name"] = contact_name

    @property
    def contact_email(self):
        """
        Set contact email
        """
        return self.mydata_config["contact_email"]

    @contact_email.setter
    def contact_email(self, contact_email):
        """
        Set contact email
        """
        self.mydata_config["contact_email"] = contact_email

    @property
    def data_directory(self):
        """
        Get root data directory
        """
        return self.mydata_config["data_directory"]

    @data_directory.setter
    def data_directory(self, data_directory):
        """
        Set root data directory
        """
        self.mydata_config["data_directory"] = data_directory

    @property
    def mytardis_url(self):
        """
        Get MyTardis URL
        """
        return self.mydata_config["mytardis_url"]

    @property
    def mytardis_api_url(self):
        """
        Get MyTardis API URL
        """
        return self.mydata_config["mytardis_url"] + "/api/v1/?format=json"

    @mytardis_url.setter
    def mytardis_url(self, mytardis_url):
        """
        Set MyTardis API URL
        """
        self.mydata_config["mytardis_url"] = (
            mytardis_url.rstrip("/") if mytardis_url else mytardis_url
        )
        self._default_owner = None
        self._instrument = None
        self._facility = None

    @property
    def username(self):
        """
        Get MyTardis username (should be a facility manager)
        """
        return self.mydata_config["username"]

    @username.setter
    def username(self, username):
        """
        Set MyTardis username (should be a facility manager)
        """
        self.mydata_config["username"] = username
        self._default_owner = None
        self._instrument = None
        self._facility = None

    @property
    def default_owner(self):
        """
        Get user model for the specified MyTardis username
        """
        from ..user import User

        if not self._default_owner:
            self._default_owner = User.get_user_by_username(self.username)
        return self._default_owner

    @default_owner.setter
    def default_owner(self, default_owner):
        """
        Set default user model for assigning experiment ACLs.
        Only used by tests.
        """
        self._default_owner = default_owner

    @property
    def api_key(self):
        """
        Get API key
        """
        return self.mydata_config["api_key"]

    @api_key.setter
    def api_key(self, api_key):
        """
        Set API key
        """
        self.mydata_config["api_key"] = api_key
        self._default_owner = None
        self._instrument = None
        self._facility = None
