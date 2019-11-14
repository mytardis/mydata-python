"""
mydata/tasks/uploads.py
"""
import mimetypes
import os

from datetime import datetime

from ..models.dataset import Dataset
from ..models.experiment import Experiment
from .lookups import Lookups
from ..models.datafile import DataFile
from ..models.upload import Upload, UploadStatus


def upload_folder(folder, lookup_callback, upload_callback):
    """
    Create required MyTardis records and upload
    any files not already uploaded.

    After each file is looked up on the MyTardis server, the lookup_callback
    function is called, passing the lookup instance of class
    mydata.models.lookup.Lookup as an argument.

    After each file is uploaded, the upload_callback
    function is called, passing the upload instance of class
    mydata.models.upload.Upload as an argument.
    """
    folder.experiment = Experiment.get_or_create_exp_for_folder(folder)
    folder.dataset = Dataset.create_dataset_if_necessary(folder)

    def lookup_cb(lookup):
        lookup_callback(lookup)
        upload_file(folder, lookup, upload_callback)

    Lookups(folder, lookup_cb).lookup_datafiles()


def upload_file(folder, lookup, upload_callback):
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

    DataFile.upload_datafile_with_post(
        datafile_path, datafile_dict,
        upload, progress_callback)

    upload_success = True
    finalize_upload(folder, upload, upload_success)

    upload_callback(upload)


def finalize_upload(folder, upload, upload_success, message=None):
    """
    Finalize upload
    """
    datafile_path = folder.get_datafile_path(upload.datafile_index)
    datafile_name = os.path.basename(datafile_path)
    if upload_success:
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
        upload.datafile_index, uploaded=upload_success)
    upload.buffered_reader.close()
