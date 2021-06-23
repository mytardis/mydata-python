"""
Model class representing a data folder which may or may not
have a corresponding dataset record in MyTardis.
"""
# pylint: disable=bare-except
import os
import time
from datetime import datetime
import hashlib
import traceback
from fnmatch import fnmatch

from ..conf import settings
from ..logs import logger

from .localfile import LocalFile


# pylint: disable=too-many-instance-attributes
class Folder:
    """
    Model class representing a data folder which may or may not
    have a corresponding dataset record in MyTardis.
    """

    # pylint: disable=too-many-public-methods
    def __init__(
        self,
        name,
        location,
        user_folder_name,
        group_folder_name,
        owner,
        group=None,
        is_exp_files_folder=False,
    ):

        self.data_view_fields = dict(
            name=name,
            location=location,
            created="",
            experiment_title="",
            status="0 of 0 files uploaded",
            owner=owner,
            group=group,
        )

        # If there are files in the top-level of an Experiment folder, not
        # within any dataset folder, then we create a special dataset to
        # collect these files:
        self.is_exp_files_folder = is_exp_files_folder

        self.local_files = []
        self.populate_local_files()

        self.user_folder_name = user_folder_name
        self.group_folder_name = group_folder_name

        self.dataset = None
        self.experiment = None

        self.num_files_uploaded = 0
        self.num_cache_hits = 0

    def populate_local_files(self):
        """
        Populate data file paths within folder object
        """
        if self.is_exp_files_folder:
            absolute_folder_path = self.location
        else:
            absolute_folder_path = os.path.join(self.location, self.name)

        for dirname, _, files in os.walk(absolute_folder_path):
            for filename in sorted(files):
                if (
                    settings.filters.use_includes_file
                    and not settings.filters.use_excludes_file
                ):
                    if not Folder.matches_includes(filename):
                        logger.debug("Ignoring %s, not matching includes." % filename)
                        continue
                elif (
                    not settings.filters.use_includes_file
                    and settings.filters.use_excludes_file
                ):
                    if Folder.matches_excludes(filename):
                        logger.debug("Ignoring %s, matching excludes." % filename)
                        continue
                elif (
                    settings.filters.use_includes_file
                    and settings.filters.use_excludes_file
                ):
                    if Folder.matches_excludes(
                        filename
                    ) and not Folder.matches_includes(filename):
                        logger.debug(
                            "Ignoring %s, matching excludes "
                            "and not matching includes." % filename
                        )
                        continue
                self.local_files.append(
                    LocalFile(
                        filepath=os.path.join(dirname, filename),
                        directory=os.path.relpath(dirname, absolute_folder_path),
                        uploaded=False,
                    )
                )
            if self.is_exp_files_folder:
                break
        self.convert_subdirs_to_mytardis_format()
        self.data_view_fields["status"] = "0 of %d files uploaded" % self.num_files

    def convert_subdirs_to_mytardis_format(self):
        """
        When we write a subdirectory path into the directory field of a
        MyTardis DataFile record, we use forward slashes, and use an
        empty string (rather than ".") to indicate that the file is in
        the dataset's top-level directory
        """
        for local_file in self.local_files:
            if local_file.directory == ".":
                local_file.directory = ""
            local_file.directory = local_file.directory.replace("\\", "/")

    def set_datafile_uploaded(self, datafile_index, uploaded):
        """
        Set a DataFile's upload status

        Used to update the number of files uploaded per folder
        displayed in the Status column of the Folders view.
        """
        self.local_files[datafile_index].uploaded = uploaded
        self.num_files_uploaded = sum(
            [local_file.uploaded for local_file in self.local_files]
        )
        self.data_view_fields["status"] = "%d of %d files uploaded" % (
            self.num_files_uploaded,
            self.num_files,
        )

    def get_datafile_path(self, datafile_index):
        """
        Get the absolute path to a file within this folder's root directory
        which is os.path.join(self.location, self.name)
        """
        return self.local_files[datafile_index].filepath

    def get_datafile_rel_path(self, datafile_index):
        """
        Get the path to a file relative to the folder's root directory
        which is os.path.join(self.location, self.name)
        """
        return os.path.relpath(
            self.get_datafile_path(datafile_index), settings.general.data_directory
        )

    def get_datafile_directory(self, datafile_index):
        """
        Get the relative path to a file's subdirectory relative to the
        folder's root directory which is
        os.path.join(self.location, self.name)
        """
        return self.local_files[datafile_index].directory

    def get_datafile_name(self, datafile_index):
        """
        Return a file's filename
        """
        return self.local_files[datafile_index].filename

    def get_datafile_size(self, datafile_index):
        """
        Return a file's size on disk
        """
        return os.stat(self.get_datafile_path(datafile_index)).st_size

    def get_datafile_created_time(self, datafile_index):
        """
        Return a file's created time on disk
        """
        absolute_file_path = self.get_datafile_path(datafile_index)
        try:
            created_time_iso_string = datetime.fromtimestamp(
                os.stat(absolute_file_path).st_ctime
            ).isoformat()
            return created_time_iso_string
        except:
            logger.error(traceback.format_exc())
            return None

    def get_datafile_modified_time(self, datafile_index):
        """
        Return a file's modified time on disk
        """
        absolute_file_path = self.get_datafile_path(datafile_index)
        try:
            modified_time_iso_string = datetime.fromtimestamp(
                os.stat(absolute_file_path).st_mtime
            ).isoformat()
            return modified_time_iso_string
        except:
            logger.error(traceback.format_exc())
            return None

    def get_rel_path(self):
        """
        Return the relative path of the folder, relative to the root
        data directory configured in MyData's settings
        """
        if self.is_exp_files_folder:
            relpath = os.path.relpath(self.location, settings.general.data_directory)
        else:
            relpath = os.path.join(
                os.path.relpath(self.location, settings.general.data_directory),
                self.name,
            )
        return relpath

    @property
    def num_files(self):
        """
        Return total number of files in this folder
        """
        return len(self.local_files)

    def set_created_date(self):
        """
        Set created date
        """
        if self.is_exp_files_folder:
            absolute_folder_path = self.location
        else:
            absolute_folder_path = os.path.join(self.location, self.name)
        self.data_view_fields["created"] = datetime.fromtimestamp(
            os.stat(absolute_folder_path).st_ctime
        ).strftime("%Y-%m-%d")

    @property
    def experiment_title(self):
        """
        Get MyTardis experiment title associated with this folder
        """
        return self.data_view_fields["experiment_title"]

    @experiment_title.setter
    def experiment_title(self, title):
        """
        Set MyTardis experiment title associated with this folder
        """
        self.data_view_fields["experiment_title"] = title

    @staticmethod
    def matches_patterns(filename, includes_or_excludes_file):
        """
        Return True if file matches at least one pattern in the includes
        or excludes file.
        """
        match = False
        with open(includes_or_excludes_file, "r") as patterns_file:
            for glob in patterns_file.readlines():
                glob = glob.strip()
                if glob == "":
                    continue
                if glob.startswith(";"):
                    continue
                if glob.startswith("#"):
                    continue
                match = match or fnmatch(filename, glob)
        return match

    @staticmethod
    def matches_includes(filename):
        """
        Return True if file matches at least one pattern in the includes
        file.
        """
        return Folder.matches_patterns(filename, settings.filters.includes_file)

    @staticmethod
    def matches_excludes(filename):
        """
        Return True if file matches at least one pattern in the excludes
        file.
        """
        return Folder.matches_patterns(filename, settings.filters.excludes_file)

    def file_is_too_new_to_upload(self, datafile_index):
        """
        Check whether this file's upload should be skipped because it has been
        modified too recently and might require further local modifications
        before its upload.
        """
        if settings.filters.ignore_new_files:
            absolute_file_path = self.get_datafile_path(datafile_index)
            too_new = (time.time() - os.path.getmtime(absolute_file_path)) <= (
                settings.filters.ignore_new_files_minutes * 60
            )
        else:
            too_new = False
        return too_new

    def calculate_md5_sum(self, datafile_index, canceled_cb=None):
        """
        Calculate MD5 checksum.

        Callbacks can be used to update progress or to indicate
        that the user canceled.
        """
        absolute_file_path = self.get_datafile_path(datafile_index)
        file_size = self.get_datafile_size(datafile_index)
        md5 = hashlib.md5()

        default_chunk_size = 128 * 1024
        max_chunk_size = 16 * 1024 * 1024
        chunk_size = default_chunk_size
        while (file_size / chunk_size) > 50 and chunk_size < max_chunk_size:
            chunk_size *= 2
        with open(absolute_file_path, "rb") as file_handle:
            # Note that the iter() func needs an empty byte string
            # for the returned iterator to halt at EOF, since read()
            # returns b'' (not just '').
            for chunk in iter(lambda: file_handle.read(chunk_size), b""):
                if canceled_cb and canceled_cb():
                    logger.debug(
                        "Aborting MD5 calculation for " "%s" % absolute_file_path
                    )
                    return None
                md5.update(chunk)
                del chunk
        return md5.hexdigest()

    def reset_counts(self):
        """
        Reset counts of uploaded files etc.
        """
        for local_file in self.local_files:
            local_file.uploaded = False

    @property
    def name(self):
        """
        The folder name, displayed in the Folder (dataset)
        column of MyData's Folders view
        """
        return self.data_view_fields["name"]

    @property
    def location(self):
        """
        The folder location, displayed in the Location
        column of MyData's Folders view
        """
        return self.data_view_fields["location"]

    @property
    def created(self):
        """
        The folder's created date/time stamp, displayed
        in the Created column of MyData's Folders view
        """
        return self.data_view_fields["created"]

    @property
    def status(self):
        """
        The folder's upload status, displayed in the
        Status column of MyData's Folders view
        """
        return self.data_view_fields["status"]

    @property
    def owner(self):
        """
        The folder's primary owner, i.e. which user should
        be granted access in the ObjectACL), displayed in
        the Owner column of MyData's Folders view
        """
        return self.data_view_fields["owner"]

    @property
    def group(self):
        """
        The group which this folder will be granted access to
        via its ObjectACL, displayed in the Group column of
        MyData's Folders view
        """
        return self.data_view_fields["group"]
