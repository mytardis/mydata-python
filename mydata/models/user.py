"""
Model class for MyTardis API v1's UserResource.
"""
import requests

from six.moves import urllib

from ..settings import SETTINGS
from ..logs import logger
from .group import Group


class User():
    """
    Model class for MyTardis API v1's UserResource.
    """
    user_not_found_string = "USER NOT FOUND IN MYTARDIS"

    def __init__(self, username=None,
                 full_name=None, email=None,
                 user_dict=None, user_not_found_in_mytardis=False):
        self.user_id = None
        self._username = username
        self._full_name = full_name
        self._email = email
        self.groups = []
        self.user_not_found_in_mytardis = user_not_found_in_mytardis

        if user_dict is not None:
            self.user_id = user_dict['id']
            if username is None:
                self._username = user_dict['username']
            if full_name is None:
                self._full_name = user_dict['first_name'] + " " + \
                    user_dict['last_name']
            if email is None:
                self._email = user_dict['email']
            for group_dict in user_dict['groups']:
                self.groups.append(Group(group_dict=group_dict))

    @property
    def username(self):
        """
        Return the username or a string indicating that
        the user was not found on the MyTardis server
        """
        if self._username:
            username = self._username
        else:
            username = User.user_not_found_string
        return username

    @username.setter
    def username(self, username):
        """
        Set the username
        """
        self._username = username

    @property
    def full_name(self):
        """
        Return the user's full name or a string indicating
        that the user was not found on the MyTardis server
        """
        if self._full_name:
            full_name = self._full_name
        else:
            full_name = User.user_not_found_string
        return full_name

    @full_name.setter
    def full_name(self, full_name):
        """
        Set the user's full name
        """
        self._full_name = full_name

    @property
    def email(self):
        """
        Return the user's email address or a string indicating
        that the user was not found on the MyTardis server
        """
        if self._email:
            email = self._email
        else:
            email = User.user_not_found_string
        return email

    @email.setter
    def email(self, email):
        """
        Set the user's email address
        """
        self._email = email

    def get_value_for_key(self, key):
        """
        Return value of field from the User model
        to display in the Users or Folders view
        """
        if hasattr(self, key) and getattr(self, key, None):
            return getattr(self, key)
        if key in ('username', 'full_name', 'email') and \
                self.user_not_found_in_mytardis:
            value = User.user_not_found_string
        else:
            value = None
        return value

    @staticmethod
    def get_user_by_username(username):
        """
        Get user by username

        :raises requests.exceptions.HTTPError:
        """
        url = "%s/api/v1/user/?format=json&username=%s" \
            % (SETTINGS.general.mytardis_url, username)
        response = requests.get(url=url, headers=SETTINGS.default_headers)
        response.raise_for_status()
        user_dicts = response.json()
        num_user_records_found = user_dicts['meta']['total_count']

        if num_user_records_found == 0:
            return None
        logger.debug("Found user record for username '" + username + "'.")
        return User(username=username, user_dict=user_dicts['objects'][0])

    @staticmethod
    def get_user_by_email(email):
        """
        Get user by email

        :raises requests.exceptions.HTTPError:
        """
        url = "%s/api/v1/user/?format=json&email__iexact=%s" \
            % (SETTINGS.general.mytardis_url,
               urllib.parse.quote(email.encode('utf-8')))
        response = requests.get(url=url, headers=SETTINGS.default_headers)
        response.raise_for_status()
        user_dicts = response.json()
        num_user_records_found = user_dicts['meta']['total_count']

        if num_user_records_found == 0:
            return None
        logger.debug("Found user record for email '" + email + "'.")
        return User(user_dict=user_dicts['objects'][0])

    @staticmethod
    def get_user_for_folder(user_folder_name, user_not_found_in_mytardis=False):
        """
        Return a User for a username or email folder

        Set user_not_found_in_mytardis to True if you already know there is
        no corresponding user record in MyTardis, but you want to create
        a "USER NOT FOUND" dummy record to render in MyData's users table.
        """
        folder_structure = SETTINGS.advanced.folder_structure
        if folder_structure.startswith("Username"):
            if user_not_found_in_mytardis:
                return User(
                    username=user_folder_name, user_not_found_in_mytardis=True)
            return User.get_user_by_username(user_folder_name)
        if folder_structure.startswith("Email"):
            if user_not_found_in_mytardis:
                return User(
                    email=user_folder_name, user_not_found_in_mytardis=True)
            return User.get_user_by_email(user_folder_name)
        return None
