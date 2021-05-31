"""
mydata/tasks/uploads.py
"""
import mimetypes
import os
import traceback

from datetime import datetime
from http.client import responses

from ..models.dataset import Dataset
from ..models.experiment import Experiment
from ..models.lookup import LookupStatus
from .lookups import FolderLookup
from ..models.datafile import DataFile
from ..models.upload import Upload, UploadStatus, UploadMethod
from ..models.upload import add_uploader_info
from ..conf import settings
from ..utils.exceptions import StorageBoxAttributeNotFound, SshException
from ..utils.openssh import upload_with_scp
from ..utils.upload import upload_file_ssh
from ..logs import logger


def upload_folder(
    folder, lookup_callback, upload_callback, upload_method=UploadMethod.SCP
):
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
    If not specified, the SCP upload method is used.
    """
    folder.experiment = Experiment.get_or_create_exp_for_folder(folder)
    folder.dataset = Dataset.create_dataset_if_necessary(folder)

    if upload_method in (UploadMethod.SCP, UploadMethod.SFTP):
        settings.uploader.request_staging_access()

    def lookup_cb(lookup):
        lookup_callback(lookup)
        if lookup.status in (
            LookupStatus.NOT_FOUND,
            LookupStatus.FOUND_UNVERIFIED_NO_DFOS,
            LookupStatus.FOUND_UNVERIFIED_ON_STAGING,
        ):
            upload_file(folder, lookup, upload_callback, upload_method)

    FolderLookup(folder, lookup_cb, upload_method).lookup_datafiles()


def upload_file(folder, lookup, upload_callback, upload_method=UploadMethod.SCP):
    """
    Upload file
    """
    # pylint: disable=too-many-locals

    upload = Upload(folder, lookup.datafile_index)

    datafile_path = folder.get_datafile_path(upload.datafile_index)

    if check_if_file_is_missing(upload, datafile_path):
        upload_callback(upload)
        return

    if check_if_file_is_too_new(folder, upload):
        upload_callback(upload)
        return

    upload.message = "Defining JSON data for POST..."
    datafile_dict = construct_datafile_post_body(folder, upload)

    if upload_method == UploadMethod.MULTIPART_POST:
        response = DataFile.upload_datafile_with_post(
            datafile_path, datafile_dict, upload
        )
        message = None
        if not response.ok:
            message = "Upload failed with HTTP %s - %s" % (
                response.status_code,
                responses[response.status_code],
            )
        finalize_upload(
            folder,
            upload,
            success=response.ok,
            message=message,
            upload_callback=upload_callback,
        )
        return

    if upload_method == UploadMethod.SCP:
        datafile_dict = add_uploader_info(datafile_dict)
        df_post_response = None
        if not lookup.existing_unverified_datafile:
            df_post_response = DataFile.create_datafile_for_staging_upload(
                datafile_dict
            )
            if not df_post_response.ok:
                err = (
                    "Creating DataFile record failed with status: %s"
                    % df_post_response.status_code
                )
                finalize_upload(
                    folder,
                    upload,
                    success=False,
                    message=str(err),
                    upload_callback=upload_callback,
                )
                return
        host, port, location, username = get_sbox_attrs(upload)
        remote_file_path = get_remote_file_path(location, lookup, df_post_response)
        upload.datafile_id = get_datafile_id(lookup, df_post_response)

        try:
            upload_via_scp_with_retries(
                datafile_path,
                username,
                host,
                port,
                remote_file_path,
                upload,
                upload_callback,
            )
        except SshException as err:
            logger.error(traceback.format_exc())
            finalize_upload(
                folder,
                upload,
                success=False,
                message=str(err),
                upload_callback=upload_callback,
            )
            return

        success = check_if_all_bytes_uploaded(upload)
        if success:
            # Request verification via MyTardis API:
            DataFile.verify(upload.datafile_id)
            finalize_upload(folder, upload, success, upload_callback=upload_callback)
        else:
            message = (
                "Marking upload as failed, because only %s of %s bytes were uploaded."
                % (upload.bytes_uploaded, upload.file_size)
            )
            finalize_upload(
                folder,
                upload,
                success,
                message=message,
                upload_callback=upload_callback,
            )
        return

    raise NotImplementedError("upload_file received unimplemented upload method")


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
    else:
        upload.status = UploadStatus.FAILED
        if not message:
            message = "Upload failed for %s" % datafile_name
        upload.message = message
    folder.set_datafile_uploaded(upload.datafile_index, uploaded=success)
    if upload_callback:
        upload_callback(upload)


def construct_datafile_post_body(folder, upload):
    """Construct DataFile dictionary to be JSON-encoded for POSTing to the API
    """
    datafile_path = folder.get_datafile_path(upload.datafile_index)

    upload.message = "Getting data file size..."
    upload.file_size = folder.get_datafile_size(upload.datafile_index)

    upload.message = "Calculating MD5 checksum..."
    md5sum = folder.calculate_md5_sum(upload.datafile_index, canceled_cb=None)

    upload.message = "Checking MIME type..."
    mime_type = mimetypes.guess_type(datafile_path)[0]
    if not mime_type:
        mime_type = "application/octet-stream"

    dataset_uri = folder.dataset.resource_uri
    created_time = folder.get_datafile_created_time(upload.datafile_index)
    modified_time = folder.get_datafile_modified_time(upload.datafile_index)
    return {
        "dataset": dataset_uri,
        "filename": os.path.basename(datafile_path),
        "directory": folder.get_datafile_directory(upload.datafile_index),
        "md5sum": md5sum,
        "size": upload.file_size,
        "mimetype": mime_type,
        "created_time": created_time,
        "modification_time": modified_time,
    }


def get_sbox_attrs(upload):
    """Get the relevant StorageBoxAttributes and StorageBoxOptions
    for SCP uploads
    """
    upload_to_staging_request = settings.uploader.upload_to_staging_request
    try:
        host = upload_to_staging_request.scp_hostname
        port = upload_to_staging_request.scp_port
        location = upload_to_staging_request.location
        username = upload_to_staging_request.scp_username
        return host, port, location, username
    except StorageBoxAttributeNotFound as err:
        upload.traceback = traceback.format_exc()
        upload.message = str(err)
        raise


def check_if_all_bytes_uploaded(upload):
    """Check if all bytes have been uploaded.

    If an exception occurs (e.g. can't connect to SCP server)
    while uploading a zero-byte file, don't want to mark it
    as completed, just because zero bytes have been uploaded.
    """
    return (
        upload.bytes_uploaded == upload.file_size
        and upload.status != UploadStatus.CANCELED
        and upload.status != UploadStatus.FAILED
    )


def upload_via_scp_with_retries(
    datafile_path, username, host, port, remote_file_path, upload, upload_callback  # pylint: disable=unused-argument
):
    """
    Upload via SCP with retries
    """
    while True:
        # Upload retries loop:
        try:
            if settings.advanced.upload_method == "SSH2":
                upload_file_ssh(
                    (host, int(port)),
                    [username, settings.uploader.ssh_key_pair.private_key_path],
                    datafile_path,
                    remote_file_path,
                    upload)
            else:
                upload_with_scp(
                    datafile_path,
                    username,
                    settings.uploader.ssh_key_pair.private_key_path,
                    host,
                    port,
                    remote_file_path,
                    upload)
            # Break out of upload retries loop.
            break
        except SshException as err:
            # includes the ScpException subclass
            upload.traceback = traceback.format_exc()
            if upload.retries < settings.advanced.max_upload_retries:
                logger.warning(str(err))
                upload.retries += 1
                logger.debug("Restarting upload for " + datafile_path)
                continue
            raise


def check_if_file_is_missing(upload, datafile_path):
    """Check if file (to be uploaded) exists on disk.

    Returns True if the file is missing.
    """
    missing = False
    if not os.path.exists(datafile_path):
        missing = True
        message = (
            "Not uploading file, because it has been moved, renamed or deleted."
        )
        upload.message = message
        upload.status = UploadStatus.FAILED
    return missing


def check_if_file_is_too_new(folder, upload):
    """Check if file is too new to be uploaded
    """
    too_new = False
    if folder.file_is_too_new_to_upload(upload.datafile_index):
        too_new = True
        message = "Not uploading file, in case it is still being modified."
        upload.message = message
        upload.status = UploadStatus.FAILED
    return too_new


def get_remote_file_path(location, lookup, df_post_response):
    """Get remote path to upload to
    """
    if lookup.existing_unverified_datafile:
        uri = lookup.existing_unverified_datafile.replicas[0].uri
        return "%s/%s" % (location.rstrip("/"), uri)
    return df_post_response.text


def get_datafile_id(lookup, response):
    """Get DataFile ID of upload
    """
    if lookup.existing_unverified_datafile:
        return lookup.existing_unverified_datafile.id
    return response.headers["Location"].split("/")[-2]
