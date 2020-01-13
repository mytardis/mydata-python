"""
mydata/tasks/lookups.py
"""
import os

import requests.exceptions

from ..models.datafile import DataFile
from ..models.lookup import Lookup, LookupStatus
from ..conf import settings
from ..threads.locks import LOCKS


class Lookups:
    """
    Methods for looking up files on a MyTardis server
    """

    def __init__(self, folder, lookup_done_cb):
        self.folder = folder
        self.lookup_done_cb = lookup_done_cb

    def lookup_datafiles(self):
        """Look up a folder's file on MyTardis
        and report whether they exist on the server and whether they are verified.
        """
        for dfi in range(0, self.folder.num_files):
            lookup = Lookup(self.folder, dfi)
            datafile_path = os.path.join(lookup.subdirectory, lookup.filename)
            datafile_dir = self.folder.get_datafile_directory(dfi)
            try:

                lookup.message = "Looking for matching file in verified files cache..."
                cache_key = "%s,%s" % (self.folder.dataset.dataset_id, datafile_path)
                if (
                    settings.miscellaneous.cache_datafile_lookups
                    and cache_key in settings.verified_datafiles_cache
                ):
                    self.folder.num_cache_hits += 1
                    self.folder.set_datafile_uploaded(dfi, True)
                    lookup.status = LookupStatus.FOUND_VERIFIED
                    self.lookup_done_cb(lookup)
                    continue

                lookup.message = "Looking for matching file on MyTardis server..."
                lookup.status = LookupStatus.IN_PROGRESS
                existing_datafile = DataFile.get_datafile(
                    dataset=self.folder.dataset,
                    filename=lookup.filename,
                    directory=datafile_dir,
                )
                if existing_datafile:
                    self.handle_existing_datafile(lookup, existing_datafile)
                else:
                    self.handle_non_existent_datafile(lookup)
            except requests.exceptions.RequestException as err:
                lookup.message = str(err)
                lookup.status = LookupStatus.FAILED
                self.lookup_done_cb(lookup)

    def handle_non_existent_datafile(self, lookup):
        """Handle lookup which found no matching file on MyTardis server
        """
        lookup.message = "Didn't find datafile on MyTardis server."
        lookup.status = LookupStatus.NOT_FOUND
        self.lookup_done_cb(lookup)

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
        datafile_path = os.path.join(lookup.subdirectory, lookup.filename)
        cache_key = "%s,%s" % (self.folder.dataset.dataset_id, datafile_path)
        if settings.miscellaneous.cache_datafile_lookups:
            with LOCKS.update_cache:  # pylint: disable=no-member
                settings.verified_datafiles_cache[cache_key] = True
        self.folder.set_datafile_uploaded(lookup.datafile_index, True)
        self.lookup_done_cb(lookup)

    def handle_existing_unverified_datafile(self, lookup, existing_datafile):
        """
        If the existing unverified DataFile was uploaded via POST, we just
        need to wait for it to be verified.  But if it was uploaded via
        staging, we might be able to resume a partial upload.
        """
        lookup.message = "Found unverified datafile record on MyTardis."

        # For now, assume we are uploading via POST:
        self.handle_unverified_unstaged_upload(lookup, existing_datafile)

    def handle_unverified_unstaged_upload(self, lookup, existing_datafile):
        """
        We found an unverified datafile on the server for which
        there is no point in checking for a resumable partial
        upload.

        This is usually because we are uploading using the POST upload method.
        Or we could be using the STAGING method but failed to find any
        DataFileObjects on the server for the datafile.
        """
        lookup.message = "Found unverified datafile record."
        # If there's an existing DFO, we probably just need to wait until
        # MyTardis verifies the file, but if there are no DFOs, MyData
        # shouldn't mark this file as uploaded:
        if existing_datafile.replicas:
            self.folder.set_datafile_uploaded(lookup.datafile_index, True)
        else:
            self.folder.set_datafile_uploaded(lookup.datafile_index, False)
        lookup.status = LookupStatus.FOUND_UNVERIFIED_UNSTAGED
        DataFile.verify(existing_datafile.datafile_id)
