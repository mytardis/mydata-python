"""
Monitor upload progress using RESTful API queries
"""
from datetime import datetime
import threading

import requests

from ..events.stop import should_cancel_upload
from ..models.datafile import DataFile
from ..models.replica import Replica
from ..models.upload import UploadStatus
from ..utils.exceptions import MissingMyDataReplicaApiEndpoint


def monitor_progress(
    progress_poll_interval, upload, file_size, monitoring_progress, progress_callback,
):
    """
    Monitor progress via RESTful queries.
    """
    if should_cancel_upload(upload) or (
        upload.status != UploadStatus.IN_PROGRESS
        and upload.status != UploadStatus.NOT_STARTED
    ):
        return

    timer = threading.Timer(
        progress_poll_interval,
        monitor_progress,
        args=[
            progress_poll_interval,
            upload,
            file_size,
            monitoring_progress,
            progress_callback,
        ],
    )
    timer.start()
    if upload.status == UploadStatus.NOT_STARTED:
        return
    if monitoring_progress.isSet():
        return
    monitoring_progress.set()
    if upload.dfo_id is None:
        if upload.datafile_id is not None:
            try:
                datafile = DataFile.get_datafile_from_id(upload.datafile_id)
                if datafile:
                    upload.dfo_id = datafile.replicas[0].dfo_id
            except requests.exceptions.RequestException:
                # If something goes wrong trying to retrieve
                # the DataFile from the MyTardis API, don't
                # worry, just try again later.
                pass
            except IndexError:
                # If the datafile.replicas[0] DFO doesn't exist yet,
                # don't worry, just check again later.
                pass
    if upload.dfo_id:
        try:
            bytes_uploaded = Replica.count_bytes_uploaded_to_staging(upload.dfo_id)
            latest_update_time = datetime.now()
            # If this file already has a partial upload in staging,
            # progress and speed estimates can be misleading.
            upload.set_latest_time(latest_update_time)
            if bytes_uploaded > upload.bytes_uploaded:
                upload.set_bytes_uploaded(bytes_uploaded)
            progress_callback(bytes_uploaded, file_size)
        except requests.exceptions.RequestException:
            timer.cancel()
        except MissingMyDataReplicaApiEndpoint:
            timer.cancel()
    monitoring_progress.clear()
