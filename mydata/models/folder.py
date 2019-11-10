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

from ..settings import SETTINGS
from ..logs import logger


class Folder(object):
    """
    Model class representing a data folder which may or may not
    have a corresponding dataset record in MyTardis.
    """
    # pylint: disable=too-many-public-methods
    def __init__(self, folder_name, location, user_folder_name,
                 group_folder_name, owner, group=None,
                 is_exp_files_folder=False):

        self.data_view_fields = dict(
            folder_name=folder_name,
            location=location,
            created="",
            experiment_title="",
            status="0 of 0 files uploaded",
            owner=owner,
            group=group)

        # If there are files in the top-level of an Experiment folder, not
        # within any dataset folder, then we create a special dataset to
        # collect these files:
        self.is_exp_files_folder = is_exp_files_folder

        self.datafile_paths = dict(
            files=[],
            directories=[],
            uploaded=[])
        self.populate_datafile_paths()

        self.user_folder_name = user_folder_name
        self.group_folder_name = group_folder_name

        self.dataset = None
        self.experiment = None

    def populate_datafile_paths(self):
        """
        Populate data file paths within folder object
        """
        if self.is_exp_files_folder:
            absolute_folder_path = self.location
        else:
            absolute_folder_path = os.path.join(self.location, self.folder_name)

        for dirname, _, files in os.walk(absolute_folder_path):
            for filename in sorted(files):
                if SETTINGS.filters.use_includes_file and \
                        not SETTINGS.filters.use_excludes_file:
                    if not Folder.matches_includes(filename):
                        logger.debug("Ignoring %s, not matching includes."
                                     % filename)
                        continue
                elif not SETTINGS.filters.use_includes_file and \
                        SETTINGS.filters.use_excludes_file:
                    if Folder.matches_excludes(filename):
                        logger.debug("Ignoring %s, matching excludes."
                                     % filename)
                        continue
                elif SETTINGS.filters.use_includes_file and \
                        SETTINGS.filters.use_excludes_file:
                    if Folder.matches_excludes(filename) and \
                            not Folder.matches_includes(filename):
                        logger.debug("Ignoring %s, matching excludes "
                                     "and not matching includes."
                                     % filename)
                        continue
                self.datafile_paths['files'].append(
                    os.path.join(dirname, filename))
                self.datafile_paths['directories']\
                    .append(os.path.relpath(dirname, absolute_folder_path))
                self.datafile_paths['uploaded'].append(False)
            if self.is_exp_files_folder:
                break
        self.convert_subdirs_to_mytardis_format()
        self.data_view_fields['status'] = \
            "0 of %d files uploaded" % self.num_files

    def convert_subdirs_to_mytardis_format(self):
        """
        When we write a subdirectory path into the directory field of a
        MyTardis DataFile record, we use forward slashes, and use an
        empty string (rather than ".") to indicate that the file is in
        the dataset's top-level directory
        """
        for i in range(0, len(self.datafile_paths['directories'])):
            if self.datafile_paths['directories'][i] == ".":
                self.datafile_paths['directories'][i] = ""
            self.datafile_paths['directories'][i] = \
                self.datafile_paths['directories'][i].replace("\\", "/")

    def set_datafile_uploaded(self, datafile_index, uploaded):
        """
        Set a DataFile's upload status

        Used to update the number of files uploaded per folder
        displayed in the Status column of the Folders view.
        """
        self.datafile_paths['uploaded'][datafile_index] = uploaded
        num_files_uploaded = sum(self.datafile_paths['uploaded'])
        self.data_view_fields['status'] = \
            "%d of %d files uploaded" % (num_files_uploaded,
                                         self.num_files)

    def get_datafile_path(self, datafile_index):
        """
        Get the absolute path to a file within this folder's root directory
        which is os.path.join(self.location, self.folder_name)
        """
        return self.datafile_paths['files'][datafile_index]

    def get_datafile_rel_path(self, datafile_index):
        """
        Get the path to a file relative to the folder's root directory
        which is os.path.join(self.location, self.folder_name)
        """
        return os.path.relpath(self.get_datafile_path(datafile_index),
                               SETTINGS.general.data_directory)

    def get_datafile_directory(self, datafile_index):
        """
        Get the relative path to a file's subdirectory relative to the
        folder's root directory which is
        os.path.join(self.location, self.folder_name)
        """
        return self.datafile_paths['directories'][datafile_index]

    def get_datafile_name(self, datafile_index):
        """
        Return a file's filename
        """
        return os.path.basename(self.datafile_paths['files'][datafile_index])

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
                os.stat(absolute_file_path).st_ctime).isoformat()
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
                os.stat(absolute_file_path).st_mtime).isoformat()
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
            relpath = os.path.relpath(
                self.location, SETTINGS.general.data_directory)
        else:
            relpath = os.path.join(
                os.path.relpath(self.location, SETTINGS.general.data_directory),
                self.folder_name)
        return relpath

    @property
    def num_files(self):
        """
        Return total number of files in this folder
        """
        return len(self.datafile_paths['files'])

    def get_value_for_key(self, key):
        """
        Used in the data view model to look up a value from a column key
        """
        if key.startswith("owner."):
            owner_key = key.split("owner.")[1]
            return self.owner.get_value_for_key(owner_key) if self.owner else None
        if key.startswith("group."):
            group_key = key.split("group.")[1]
            return self.group.get_value_for_key(group_key) if self.group else None
        return getattr(self, key)

    def set_created_date(self):
        """
        Set created date
        """
        if self.is_exp_files_folder:
            absolute_folder_path = self.location
        else:
            absolute_folder_path = os.path.join(self.location, self.folder_name)
        self.data_view_fields['created'] = datetime.fromtimestamp(
            os.stat(absolute_folder_path).st_ctime)\
            .strftime('%Y-%m-%d')

    @property
    def experiment_title(self):
        """
        Get MyTardis experiment title associated with this folder
        """
        return self.data_view_fields['experiment_title']

    @experiment_title.setter
    def experiment_title(self, title):
        """
        Set MyTardis experiment title associated with this folder
        """
        self.data_view_fields['experiment_title'] = title

    @staticmethod
    def matches_patterns(filename, includes_or_excludes_file):
        """
        Return True if file matches at least one pattern in the includes
        or excludes file.
        """
        match = False
        with open(includes_or_excludes_file, 'r') as patterns_file:
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
        return Folder.matches_patterns(
            filename, SETTINGS.filters.includes_file)

    @staticmethod
    def matches_excludes(filename):
        """
        Return True if file matches at least one pattern in the excludes
        file.
        """
        return Folder.matches_patterns(
            filename, SETTINGS.filters.excludes_file)

    def file_is_too_new_to_upload(self, datafile_index):
        """
        Check whether this file's upload should be skipped because it has been
        modified too recently and might require further local modifications
        before its upload.
        """
        if SETTINGS.filters.ignore_new_files:
            absolute_file_path = self.get_datafile_path(datafile_index)
            too_new = (time.time() - os.path.getmtime(absolute_file_path)) <= \
                (SETTINGS.filters.ignore_new_files_minutes * 60)
        else:
            too_new = False
        return too_new

    def calculate_md5_sum(self, datafile_index, progress_callback=None,
                          canceled_callback=None):
        """
        Calculate MD5 checksum.
        """
        absolute_file_path = self.get_datafile_path(datafile_index)
        file_size = self.get_datafile_size(datafile_index)
        md5 = hashlib.md5()

        default_chunk_size = 128 * 1024
        max_chunk_size = 16 * 1024 * 1024
        chunk_size = default_chunk_size
        while (file_size / chunk_size) > 50 and chunk_size < max_chunk_size:
            chunk_size *= 2
        bytes_processed = 0
        with open(absolute_file_path, 'rb') as file_handle:
            # Note that the iter() func needs an empty byte string
            # for the returned iterator to halt at EOF, since read()
            # returns b'' (not just '').
            for chunk in iter(lambda: file_handle.read(chunk_size), b''):
                if canceled_callback():
                    logger.debug("Aborting MD5 calculation for "
                                 "%s" % absolute_file_path)
                    return None
                md5.update(chunk)
                bytes_processed += len(chunk)
                del chunk
                if progress_callback:
                    progress_callback(bytes_processed)
        return md5.hexdigest()

    def reset_counts(self):
        """
        Reset counts of uploaded files etc.
        """
        self.datafile_paths['uploaded'] = []
        for _ in range(0, self.num_files):
            self.datafile_paths['uploaded'].append(False)

    @property
    def folder_name(self):
        """
        The folder name, displayed in the Folder (dataset)
        column of MyData's Folders view
        """
        return self.data_view_fields['folder_name']

    @property
    def location(self):
        """
        The folder location, displayed in the Location
        column of MyData's Folders view
        """
        return self.data_view_fields['location']

    @property
    def created(self):
        """
        The folder's created date/time stamp, displayed
        in the Created column of MyData's Folders view
        """
        return self.data_view_fields['created']

    @property
    def status(self):
        """
        The folder's upload status, displayed in the
        Status column of MyData's Folders view
        """
        return self.data_view_fields['status']

    @property
    def owner(self):
        """
        The folder's primary owner, i.e. which user should
        be granted access in the ObjectACL), displayed in
        the Owner column of MyData's Folders view
        """
        return self.data_view_fields['owner']

    @property
    def group(self):
        """
        The group which this folder will be granted access to
        via its ObjectACL, displayed in the Group column of
        MyData's Folders view
        """
        return self.data_view_fields['group']
