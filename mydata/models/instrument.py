"""
Model class for MyTardis API v1's InstrumentResource.
"""
import json
import urllib.parse

import requests

from ..conf import settings
from ..logs import logger
from ..utils.exceptions import DuplicateKey
from .facility import Facility


class Instrument():
    """
    Model class for MyTardis API v1's InstrumentResource.
    """
    def __init__(self, name, instrument_dict):
        self.name = name
        self.json = instrument_dict
        self.instrument_id = instrument_dict['id']
        self.facility = Facility(facility_dict=instrument_dict['facility'])

    @property
    def resource_uri(self):
        """
        Return the API resource URI..
        """
        return self.json['resource_uri']

    @staticmethod
    def create_instrument(facility, name):
        """
        Create instrument.

        :raises requests.exceptions.HTTPError:
        """
        url = "%s/api/v1/instrument/" % settings.general.mytardis_url
        instrument_dict = {
            "facility": facility.resource_uri,
            "name": name}
        data = json.dumps(instrument_dict)
        headers = settings.default_headers
        response = requests.post(headers=headers, url=url, data=data.encode())
        response.raise_for_status()
        instrument_dict = response.json()
        return Instrument(name=name, instrument_dict=instrument_dict)

    @staticmethod
    def get_instrument(facility, name):
        """
        Get instrument.

        :raises requests.exceptions.HTTPError:
        """
        url = "%s/api/v1/instrument/?format=json&facility__id=%s&name=%s" \
            % (settings.general.mytardis_url, facility.facility_id,
               urllib.parse.quote(name.encode('utf-8')))
        response = requests.get(url=url, headers=settings.default_headers)
        response.raise_for_status()
        instruments_dict = response.json()
        num_instruments_found = \
            instruments_dict['meta']['total_count']
        if num_instruments_found == 0:
            message = "Instrument \"%s\" was not found in MyTardis" % name
            logger.warning(message)
            return None
        logger.debug("Found instrument record for name \"%s\" "
                     "in facility \"%s\"" % (name, facility.name))
        instrument_dict = instruments_dict['objects'][0]
        return Instrument(name=name, instrument_dict=instrument_dict)

    @staticmethod
    def rename_instrument(facility_name, old_name, new_name):
        """
        Rename the instrument
        """
        facilities = Facility.get_my_facilities()
        facility = None
        for facil in facilities:
            if facility_name == facil.name:
                facility = facil
                break
        if facility is None:
            raise Exception("Facility is None in rename_instrument.")
        old_instrument = \
            Instrument.get_instrument(facility, old_name)
        if not old_instrument:
            raise Exception("Instrument record for old instrument "
                            "name not found in rename_instrument.")
        duplicate = Instrument.get_instrument(facility, new_name)
        if duplicate:
            raise DuplicateKey("Instrument with name \"%s\" "
                               "already exists" % new_name)
        old_instrument.rename(new_name)

    def rename(self, name):
        """
        Rename instrument.

        :raises requests.exceptions.HTTPError:
        """
        logger.info("Renaming instrument \"%s\" to \"%s\"."
                    % (str(self), name))
        url = "%s/api/v1/instrument/%d/" \
            % (settings.general.mytardis_url, self.instrument_id)
        uploader_dict = {"name": name}
        data = json.dumps(uploader_dict)
        headers = settings.default_headers
        response = requests.put(headers=headers, url=url, data=data.encode())
        response.raise_for_status()
        logger.info("Renaming instrument succeeded.")
