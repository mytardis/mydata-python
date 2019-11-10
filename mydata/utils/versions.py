"""
The MyDataVersions class contains methods to determine whether we are running
the latest official version, an older version, or a newer version.
"""
# pylint: disable=bare-except
from datetime import datetime
import json
import os
import pickle

import dateutil.parser
import pytz
import requests

from ..settings import SETTINGS

from ..logs import logger

GITHUB_API_BASE_URL = "https://api.github.com/repos/mytardis/mydata"
CACHE_REFRESH_INTERVAL = 300  # seconds


class MyDataVersions():
    """
    The MyDataVersions class contains methods to determine whether we are
    running the latest official version, an older version, or a newer
    version.

    The GitHub API will throttle more than 60 connections per hour from the
    same IP address which I can easily reach while testing MyData, so we cache
    results from GitHub API queries.
    """
    def __init__(self):
        self._latest_official_release = None
        self._latest_releases = None
        self._tags_cache = None

    @property
    def latest_official_release(self):
        """
        Gets the latest official release from the GitHub API.

        :raises requests.exceptions.HTTPError:
        """
        if self._latest_official_release:
            return self._latest_official_release
        interval = datetime.utcnow().replace(tzinfo=pytz.utc) - \
            self.latest_official_release_cache_time
        if interval.total_seconds() > CACHE_REFRESH_INTERVAL:
            url = "%s/releases/latest" % GITHUB_API_BASE_URL
            logger.debug(url)
            response = requests.get(url)
            response.raise_for_status()
            self._latest_official_release = response.json()
            with open(self.latest_official_release_cache_path, 'w') as cache:
                cache.write(response.text)
        else:
            with open(self.latest_official_release_cache_path, 'r') as cache:
                self._latest_official_release = json.load(cache)
        return self._latest_official_release

    @property
    def latest_official_release_tag_name(self):
        """
        Gets the tag for the latest official release.
        """
        return self.latest_official_release['tag_name']

    @property
    def latest_official_release_body(self):
        """
        Gets the body for the latest official release.
        """
        body = self.latest_official_release['body']
        lines = body.split('\n')
        body = ""
        for line in lines:
            if line.strip() != "```":
                body += "%s\n" % line
        return body

    @property
    def latest_official_release_date_time(self):
        """
        Returns the date and time (UTC) of the latest official release.
        """
        return dateutil.parser.parse(
            self.latest_official_release['published_at'])

    @property
    def latest_official_release_cache_path(self):
        """
        Response from
        https://api.github.com/repos/mytardis/mydata/releases/latest
        is cached to avoid throttling (only 60 requests are allowed
        per hour from the same IP address).  Throttling is unlikely
        to be an issue in production, but in development, running MyData
        more than 60 times within an hour is common.
        """
        assert SETTINGS.config_path
        return os.path.join(
            os.path.dirname(SETTINGS.config_path),
            "latest-official-release.json")

    @property
    def latest_official_release_cache_time(self):
        """
        Return time when the latest version cache was last updated.
        """
        try:
            return datetime.utcfromtimestamp(
                os.path.getmtime(self.latest_official_release_cache_path)) \
                .replace(tzinfo=pytz.utc)
        except (OSError, IOError):
            return datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)

    @property
    def latest_releases(self):
        """
        Gets the latest 30 releases from the GitHub API.
        30 is the default number of releases per page in the GitHub API.

        They are in reverse chronological order (most recent first).

        :raises requests.exceptions.HTTPError:
        """
        if self._latest_releases:
            return self._latest_releases
        interval = datetime.utcnow().replace(tzinfo=pytz.utc) - \
            self.latest_releases_cache_time
        if interval.total_seconds() > CACHE_REFRESH_INTERVAL:
            url = "%s/releases" % GITHUB_API_BASE_URL
            logger.debug(url)
            response = requests.get(url)
            response.raise_for_status()
            self._latest_releases = response.json()
            with open(self.latest_releases_cache_path, 'w') as cache:
                cache.write(response.text)
        else:
            with open(self.latest_releases_cache_path, 'r') as cache:
                self._latest_releases = json.load(cache)
        return self._latest_releases

    @property
    def latest_releases_cache_path(self):
        """
        Response from
        https://api.github.com/repos/mytardis/mydata/releases
        is cached to avoid throttling (only 60 requests are allowed
        per hour from the same IP address).  Throttling is unlikely
        to be an issue in production, but in development, running MyData
        more than 60 times within an hour is common.
        """
        assert SETTINGS.config_path
        return os.path.join(
            os.path.dirname(SETTINGS.config_path), "latest-releases.json")

    @property
    def latest_releases_cache_time(self):
        """
        Return time when the latest releases cache was last updated.
        """
        try:
            return datetime.utcfromtimestamp(
                os.path.getmtime(self.latest_releases_cache_path)) \
                .replace(tzinfo=pytz.utc)
        except (OSError, IOError):
            return datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)

    @property
    def latest_release_tag_name(self):
        """
        Gets the tag for the latest release.
        """
        if self.latest_releases:
            tag = self.latest_releases[0]['tag_name']
        else:
            tag = None
        return tag

    @property
    def latest_release_body(self):
        """
        Gets the body for the latest release.

        MyData release notes (body) tend to begin with ``` and end with ```
        so that they will be displayed in a fixed width font.
        """
        if self.latest_releases:
            body = self.latest_releases[0]['body']
            lines = body.split('\n')
            body = ""
            for line in lines:
                if line.strip() != "```":
                    body += "%s\n" % line
        else:
            body = None
        return body

    @property
    def latest_release_date_time(self):
        """
        Returns the date and time (UTC) of the latest release.
        """
        if self.latest_releases:
            published_at = self.latest_releases[0]['published_at']
            latest_time = dateutil.parser.parse(published_at)
        else:
            latest_time = None
        return latest_time

    @property
    def latest_release_is_prerelease(self):
        """
        Returns True if the latest release is a pre-release.
        """
        if self.latest_releases:
            is_pre_release = self.latest_releases[0]['prerelease']
        else:
            is_pre_release = None
        return is_pre_release

    @property
    def tags_cache_path(self):
        """
        Responses from
        https://api.github.com/repos/mytardis/mydata/git/refs/tags/[tag]
        are cached to avoid throttling (only 60 requests are allowed
        per hour from the same IP address).
        """
        assert SETTINGS.config_path
        return os.path.join(
            os.path.dirname(SETTINGS.config_path), "tags.pkl")

    @property
    def tags_cache(self):
        """
        We use a serialized dictionary to cache DataFile lookup results.
        We'll use a separate cache file for each MyTardis server we connect to.
        """
        if not self._tags_cache:
            if os.path.exists(self.tags_cache_path):
                try:
                    with open(self.tags_cache_path, 'rb') as cache_file:
                        self._tags_cache = pickle.load(cache_file)
                except:
                    self._tags_cache = dict()
            else:
                self._tags_cache = dict()
        return self._tags_cache

    def save_tags_cache(self):
        """
        Save tags cache to disk
        """
        with open(self.tags_cache_path, 'wb') as cache_file:
            pickle.dump(self._tags_cache, cache_file)

    def get_tag(self, tag_name):
        """
        Gets the latest official release's tag from the GitHub API.

        :raises requests.exceptions.HTTPError:
        """
        if tag_name in self.tags_cache:
            return self.tags_cache[tag_name]
        url = "%s/git/refs/tags/%s" % (GITHUB_API_BASE_URL, tag_name)
        logger.debug(url)
        response = requests.get(url)
        response.raise_for_status()
        tag = response.json()
        self.tags_cache[tag_name] = tag
        self.save_tags_cache()
        return tag

    @property
    def latest_official_release_commit_hash(self):
        """
        Return the SHA-1 commit hash for the latest official release.
        """
        tag_name = self.latest_official_release_tag_name
        tag = self.get_tag(tag_name)
        return tag['object']['sha']

    @property
    def latest_release_commit_hash(self):
        """
        Return the SHA-1 commit hash for the latest release.
        """
        tag_name = self.latest_release_tag_name
        tag = self.get_tag(tag_name)
        return tag['object']['sha']


MYDATA_VERSIONS = MyDataVersions()
