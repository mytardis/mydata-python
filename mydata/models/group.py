"""
Model class for MyTardis API v1's GroupResource.
"""
import urllib.parse

import requests

from ..conf import settings
from ..logs import logger


class Group:
    """
    Model class for MyTardis API v1's GroupResource.
    """

    def __init__(
        self,
        name=None,
        group_dict=None,
        group_folder_name=None,
        group_not_found_in_mytardis=False,
    ):
        self.group_folder_name = group_folder_name
        self.id = None  # pylint: disable=invalid-name
        self.name = name
        self.group_dict = group_dict
        self.group_not_found_in_mytardis = group_not_found_in_mytardis

        if group_dict is not None:
            self.id = group_dict["id"]
            if name is None:
                self.name = group_dict["name"]

        self.short_name = name
        length = len(settings.advanced.group_prefix)
        self.short_name = self.name[length:]

    def get_value_for_key(self, key):
        """
        Return value of field from the Group model
        to display in the Groups or Folders view
        """
        return getattr(self, key)

    @staticmethod
    def get_group_by_name(name, group_folder_name=None):
        """Return the group record matching the supplied name

        :raises requests.exceptions.HTTPError:
        """
        group_folder_name = group_folder_name or name
        url = "%s/api/v1/group/?format=json&name=%s" % (
            settings.general.mytardis_url,
            urllib.parse.quote(name.encode("utf-8")),
        )
        response = requests.get(url=url, headers=settings.default_headers)
        response.raise_for_status()
        groups_dict = response.json()
        num_groups_found = groups_dict["meta"]["total_count"]

        if num_groups_found == 0:
            return None
        logger.debug("Found group record for name '" + name + "'.")
        return Group(
            name=name,
            group_dict=groups_dict["objects"][0],
            group_folder_name=group_folder_name,
        )

    @staticmethod
    def get_group_for_folder(group_folder_name, group_not_found_in_mytardis=False):
        """Return a Group for a group folder

        Set user_not_found_in_mytardis to True if you already know there is
        no corresponding group record in MyTardis, but you want to create
        a "GROUP NOT FOUND" dummy record.
        """
        group_name = settings.advanced.group_prefix + group_folder_name
        if group_not_found_in_mytardis:
            return Group(
                name=group_name,
                group_folder_name=group_folder_name,
                group_not_found_in_mytardis=True,
            )
        return Group.get_group_by_name(
            name=group_name, group_folder_name=group_folder_name
        )
