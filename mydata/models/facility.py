"""
Model class for MyTardis API v1's FacilityResource.
"""

import requests

from ..settings import SETTINGS
from .group import Group


class Facility():
    """
    Model class for MyTardis API v1's FacilityResource.
    """
    def __init__(self, name=None, facility_dict=None):
        self.facility_id = None
        self.name = name
        self.json = facility_dict
        self.manager_group = None

        if facility_dict is not None:
            self.facility_id = facility_dict['id']
            if name is None:
                self.name = facility_dict['name']
            self.manager_group = \
                Group(group_dict=facility_dict['manager_group'])

    @property
    def resource_uri(self):
        """
        Return the API resource URI.
        """
        return self.json['resource_uri']

    @staticmethod
    def get_my_facilities():
        """
        Get facilities I have access to (by
        facility managers group membership).

        :raises requests.exceptions.HTTPError:
        """
        facilities = []
        url = "%s/api/v1/facility/?format=json" % SETTINGS.general.mytardis_url
        response = requests.get(url=url, headers=SETTINGS.default_headers)
        response.raise_for_status()
        facilities_dict = response.json()
        for facility_dict in facilities_dict['objects']:
            facilities.append(Facility(facility_dict=facility_dict))
        return facilities
