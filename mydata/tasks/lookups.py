"""
mydata/tasks/lookups.py
"""
import os

import requests.exceptions

from ..models.datafile import DataFile
from ..models.lookup import Lookup, LookupStatus
from ..models.upload import UploadMethod
from ..conf import settings
from ..threads.locks import LOCKS


class FolderLookup:
    """Methods for looking up files on a MyTardis server

    This class handles a request to lookup a whole folder or files.

    Each individual file lookup can be handled by a separate thread.
    """

    def __init__(self, folder, lookup_done_cb, upload_method):
        self.folder = folder
        self.lookup_done_cb = lookup_done_cb
        self.upload_method = upload_method

    def lookup_datafiles(self):
        """Look up a folder's files on MyTardis
        and report whether they exist on the server and whether they are verified.
        """
        for dfi in range(0, self.folder.num_files):
            lookup_runnable = LookupRunnable(self, dfi)
            lookup_runnable.lookup_datafile()


class LookupRunnable:
    """Methods for looking up files on a MyTardis server

    This class handles a single file lookup, identified by
    a DataFileIndex (dfi) associated with a folder_lookup's folder instance.

    Instances of this class can be added to a Queue consumed by multiple
    worker threads, which each thread calling the lookup_datafile method
    of the supplied LookupRunnable instance.
    """

    def __init__(self, folder_lookup, dfi):
        self.folder_lookup = folder_lookup
        self.dfi = dfi

    def lookup_datafile(self):
        """Look up a single file on the MyTardis server and determine whether
        it is verified.

        This method is designed to be thread-safe, i.e. multiple instances of
        LookupRunnable can have this method invoked concurrently.
        """
        folder = self.folder_lookup.folder

        lookup = Lookup(folder, self.dfi)
        datafile_path = os.path.join(lookup.subdirectory, lookup.filename)
        datafile_dir = folder.get_datafile_directory(self.dfi)
        try:

            lookup.message = "Looking for matching file in verified files cache..."
            cache_key = "%s,%s" % (folder.dataset.dataset_id, datafile_path)
            if (
                settings.miscellaneous.cache_datafile_lookups
                and cache_key in settings.verified_datafiles_cache
            ):
                folder.num_cache_hits += 1
                folder.set_datafile_uploaded(self.dfi, True)
                lookup.status = LookupStatus.FOUND_VERIFIED
                self.folder_lookup.lookup_done_cb(lookup)
                return

            lookup.message = "Looking for matching file on MyTardis server..."
            lookup.status = LookupStatus.IN_PROGRESS
            existing_datafile = DataFile.get_datafile(
                dataset=folder.dataset,
                filename=lookup.filename,
                directory=datafile_dir,
            )
            if existing_datafile:
                self.handle_existing_datafile(lookup, existing_datafile)
            else:
                self.handle_non_existent_datafile(lookup)
        except requests.exceptions.RequestException as err:
            if err.request.method == "GET":
                lookup.message = str(err)
                lookup.status = LookupStatus.FAILED
                self.folder_lookup.lookup_done_cb(lookup)
            else:
                raise

    def handle_non_existent_datafile(self, lookup):
        """Handle lookup which found no matching file on MyTardis server
        """
        lookup.message = "Didn't find datafile on MyTardis server."
        lookup.status = LookupStatus.NOT_FOUND
        self.folder_lookup.lookup_done_cb(lookup)

    def handle_existing_datafile(self, lookup, existing_datafile):
        """Check if existing DataFile is verified
        """
        lookup.message = "Found datafile on MyTardis server."
        if not existing_datafile.replicas or not existing_datafile.replicas[0].verified:
            self.handle_existing_unverified_datafile(lookup, existing_datafile)
        else:
            lookup.status = LookupStatus.FOUND_VERIFIED
            self.handle_existing_verified_datafile(lookup)

    def handle_existing_verified_datafile(self, lookup):
        """Found existing verified file on server
        """
        folder = self.folder_lookup.folder
        datafile_path = os.path.join(lookup.subdirectory, lookup.filename)
        cache_key = "%s,%s" % (folder.dataset.dataset_id, datafile_path)
        if settings.miscellaneous.cache_datafile_lookups:
            with LOCKS.update_cache:  # pylint: disable=no-member
                settings.verified_datafiles_cache[cache_key] = True
        folder.set_datafile_uploaded(lookup.datafile_index, True)
        self.folder_lookup.lookup_done_cb(lookup)

    def handle_existing_unverified_datafile(self, lookup, existing_datafile):
        """
        If the existing unverified DataFile was uploaded via POST, we just
        need to wait for it to be verified.  But if it was uploaded via
        staging, we might be able to resume a partial upload.
        """
        lookup.message = "Found unverified datafile record on MyTardis."

        if self.folder_lookup.upload_method == UploadMethod.SCP:
            self.handle_unverified_file_on_staging(lookup, existing_datafile)
        else:
            self.handle_unverified_unstaged_upload(lookup, existing_datafile)

    def handle_unverified_file_on_staging(self, lookup, existing_datafile):
        """
        Re-upload file (resuming partial uploads is not supported).
        """
        folder = self.folder_lookup.folder
        lookup.message = "Found unverified file while using upload-via-staging."
        lookup.existing_unverified_datafile = existing_datafile
        if existing_datafile.replicas:
            folder.set_datafile_uploaded(lookup.datafile_index, False)
            lookup.status = LookupStatus.FOUND_UNVERIFIED_ON_STAGING
        else:
            folder.set_datafile_uploaded(lookup.datafile_index, False)
            lookup.status = LookupStatus.FOUND_UNVERIFIED_NO_DFOS
        self.folder_lookup.lookup_done_cb(lookup)

    def handle_unverified_unstaged_upload(self, lookup, existing_datafile):
        """
        We found an unverified datafile on the server but because
        we are using POST to create and upload the DataFile at the same time,
        we can't try re-uploading the file, like we can when using the
        SCP via Staging upload method.
        """
        folder = self.folder_lookup.folder
        lookup.message = "Found unverified datafile record."
        # If there's an existing DFO, we probably just need to wait until
        # MyTardis verifies the file, but if there are no DFOs, MyData
        # should not mark this file as uploaded:
        if existing_datafile.replicas:
            folder.set_datafile_uploaded(lookup.datafile_index, True)
            lookup.status = LookupStatus.FOUND_UNVERIFIED_UNSTAGED
            DataFile.verify(existing_datafile.id)
        else:
            folder.set_datafile_uploaded(lookup.datafile_index, False)
            lookup.status = LookupStatus.FOUND_UNVERIFIED_NO_DFOS
        self.folder_lookup.lookup_done_cb(lookup)
