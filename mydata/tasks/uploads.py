"""
mydata/tasks/uploads.py
"""
import mimetypes
import os
import traceback

from datetime import datetime

from ..models.dataset import Dataset
from ..models.experiment import Experiment
from ..models.lookup import LookupStatus
from .lookups import Lookups
from ..models.datafile import DataFile
from ..models.upload import Upload, UploadStatus, UploadMethod
from ..models.upload import add_uploader_info
from ..settings import SETTINGS
from ..utils.exceptions import StorageBoxAttributeNotFound, SshException
from ..utils.openssh import upload_with_scp
from ..logs import logger


def upload_folder(
        folder, lookup_callback, upload_callback, upload_method=UploadMethod.SCP):
    """
    Create required MyTardis records and upload
    any files not already uploaded.

    After each file is looked up on the MyTardis server, the lookup_callback
    function is called, passing the lookup instance of class
    mydata.models.lookup.Lookup as an argument.

    After each file is uploaded, the upload_callback
    function is called, passing the upload instance of class
    mydata.models.upload.Upload as an argument.

    upload_method (if specified) should be a value from the
    mydata.models.upload.UploadMethod enumerated data type.
    If not specified, the SCP
    """
    folder.experiment = Experiment.get_or_create_exp_for_folder(folder)
    folder.dataset = Dataset.create_dataset_if_necessary(folder)

    if upload_method in (UploadMethod.SCP, UploadMethod.SFTP):
        SETTINGS.uploader.request_staging_access()

    def lookup_cb(lookup):
        lookup_callback(lookup)
        if lookup.status == LookupStatus.NOT_FOUND:
            upload_file(folder, lookup, upload_callback, upload_method)

    Lookups(folder, lookup_cb).lookup_datafiles()


def upload_file(folder, lookup, upload_callback, upload_method=UploadMethod.SCP):
    """
    Upload file
    """
    upload = Upload(folder, lookup.datafile_index)

    datafile_path = folder.get_datafile_path(upload.datafile_index)

    if not os.path.exists(datafile_path) or \
            folder.file_is_too_new_to_upload(upload.datafile_index):
        if not os.path.exists(datafile_path):
            message = ("Not uploading file, because it has been "
                       "moved, renamed or deleted.")
        else:
            message = ("Not uploading file, "
                       "in case it is still being modified.")
        upload.message = message
        upload.status = UploadStatus.FAILED
        upload_callback(upload)
        return

    upload.message = "Getting data file size..."
    upload.file_size = folder.get_datafile_size(upload.datafile_index)

    upload.message = "Calculating MD5 checksum..."

    md5sum = folder.calculate_md5_sum(
        upload.datafile_index, progress_cb=None, canceled_cb=None)

    datafile_dict = None
    upload.message = "Checking MIME type..."
    mime_type = mimetypes.MimeTypes().guess_type(datafile_path)[0]

    upload.message = "Defining JSON data for POST..."
    dataset_uri = folder.dataset.resource_uri
    created_time = folder.get_datafile_created_time(upload.datafile_index)
    modified_time = folder.get_datafile_modified_time(upload.datafile_index)
    datafile_dict = {
        "dataset": dataset_uri,
        "filename": os.path.basename(datafile_path),
        "directory": folder.get_datafile_directory(
            upload.datafile_index),
        "md5sum": md5sum,
        "size": md5sum,
        "mimetype": mime_type,
        "created_time": created_time,
        "modification_time": modified_time,
    }

    def progress_callback():
        pass

    if upload_method == UploadMethod.MULTIPART_POST:
        DataFile.upload_datafile_with_post(
            datafile_path, datafile_dict,
            upload, progress_callback)
    elif upload_method == UploadMethod.SCP:
        datafile_dict = add_uploader_info(datafile_dict)
        response = None
        if not lookup.existing_unverified_datafile:
            response = DataFile.create_datafile_for_staging_upload(datafile_dict)
            response.raise_for_status()
        upload_to_staging_request = SETTINGS.uploader.upload_to_staging_request
        assert upload_to_staging_request
        try:
            host = upload_to_staging_request.scp_hostname
            port = upload_to_staging_request.scp_port
            location = upload_to_staging_request.location
            username = upload_to_staging_request.scp_username
        except StorageBoxAttributeNotFound as err:
            upload.traceback = traceback.format_exc()
            upload.message = str(err)
            raise
        if lookup.existing_unverified_datafile:
            uri = lookup.existing_unverified_datafile.replicas[0].uri
            remote_file_path = "%s/%s" % (location.rstrip('/'), uri)
        else:
            # DataFile creation via the MyTardis API doesn't
            # return JSON, but if a DataFile record is created
            # without specifying a storage location, then a
            # temporary location is returned for the client
            # to copy/upload the file to.
            remote_file_path = response.text
            datafile_id = response.headers['Location'].split('/')[-2]
            upload.datafile_id = datafile_id

        while True:
            # Upload retries loop:
            try:
                progress_cb = None
                upload_with_scp(
                    datafile_path, username,
                    SETTINGS.uploader.ssh_key_pair.private_key_path,
                    host, port, remote_file_path, progress_cb, upload)
                # Break out of upload retries loop.
                break
            except SshException as err:
                # includes the ScpException subclass
                upload.traceback = traceback.format_exc()
                if upload.retries < SETTINGS.advanced.max_upload_retries:
                    logger.warning(str(err))
                    upload.retries += 1
                    logger.debug("Restarting upload for " + datafile_path)
                    upload.set_progress(0)
                    continue
                logger.error(traceback.format_exc())
                message = str(err)
                finalize_upload(folder, upload, success=False, message=str(err),
                                upload_callback=upload_callback)
                return

        # If an exception occurs (e.g. can't connect to SCP server)
        # while uploading a zero-byte file, don't want to mark it
        # as completed, just because zero bytes have been uploaded.
        if upload.bytes_uploaded == upload.file_size and \
                upload.status != UploadStatus.CANCELED and \
                upload.status != UploadStatus.FAILED:
            success = True
            if lookup.existing_unverified_datafile:
                datafile_id = lookup.existing_unverified_datafile.id
            else:
                location = response.headers['location']
                datafile_id = location.split("/")[-2]

            # Request verification via MyTardis API
            # POST-uploaded files are verified automatically by MyTardis, but
            # for staged files, we need to request verification after
            # uploading to staging.
            DataFile.verify(datafile_id)
            finalize_upload(folder, upload, success, upload_callback=upload_callback)
        else:
            success = False
            message = ("Marking upload as failed, because only %s of %s bytes were uploaded."
                       % (upload.bytes_uploaded, upload.file_size))
            finalize_upload(folder, upload, success, message=message,
                            upload_callback=upload_callback)
        return
    else:
        raise NotImplementedError(
            "upload_file received unimplemented upload method")

    success = True
    finalize_upload(folder, upload, success, upload_callback=upload_callback)


def finalize_upload(folder, upload, success, message=None, upload_callback=None):
    """
    Finalize upload
    """
    datafile_path = folder.get_datafile_path(upload.datafile_index)
    datafile_name = os.path.basename(datafile_path)
    if success:
        upload.status = UploadStatus.COMPLETED
        if not message:
            message = "Upload complete!"
        upload.message = message
        upload.set_latest_time(datetime.now())
        upload.set_progress(100)
    else:
        upload.status = UploadStatus.FAILED
        if not message:
            message = "Upload failed for %s" % datafile_name
        upload.message = message
        upload.set_progress(0)
    folder.set_datafile_uploaded(
        upload.datafile_index, uploaded=success)
    if upload_callback:
        upload_callback(upload)
