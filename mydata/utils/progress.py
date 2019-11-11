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
from ..utils.exceptions import DoesNotExist
from ..utils.exceptions import MissingMyDataReplicaApiEndpoint


def monitor_progress(progress_poll_interval, upload_model,
                     file_size, monitoring_progress, progress_callback):
    """
    Monitor progress via RESTful queries.
    """
    if should_cancel_upload(upload_model) or \
            (upload_model.status != UploadStatus.IN_PROGRESS and
             upload_model.status != UploadStatus.NOT_STARTED):
        return

    timer = threading.Timer(
        progress_poll_interval, monitor_progress,
        args=[progress_poll_interval, upload_model, file_size,
              monitoring_progress, progress_callback])
    timer.start()
    if upload_model.status == UploadStatus.NOT_STARTED:
        return
    if monitoring_progress.isSet():
        return
    monitoring_progress.set()
    if upload_model.dfo_id is None:
        if upload_model.datafile_id is not None:
            try:
                datafile = DataFile.get_datafile_from_id(
                    upload_model.datafile_id)
                upload_model.dfo_id = datafile.replicas[0].dfo_id
            except requests.exceptions.RequestException:
                # If something goes wrong trying to retrieve
                # the DataFile from the MyTardis API, don't
                # worry, just try again later.
                pass
            except DoesNotExist:
                # If the DataFile ID reported in the location header
                # after POSTing to the API doesn't exist yet, don't
                # worry, just check again later.
                pass
            except IndexError:
                # If the datafile.replicas[0] DFO doesn't exist yet,
                # don't worry, just check again later.
                pass
    if upload_model.dfo_id:
        try:
            bytes_uploaded = \
                Replica.count_bytes_uploaded_to_staging(upload_model.dfo_id)
            latest_update_time = datetime.now()
            # If this file already has a partial upload in staging,
            # progress and speed estimates can be misleading.
            upload_model.set_latest_time(latest_update_time)
            if bytes_uploaded > upload_model.bytes_uploaded:
                upload_model.set_bytes_uploaded(bytes_uploaded)
            progress_callback(bytes_uploaded, file_size)
        except requests.exceptions.RequestException:
            timer.cancel()
        except MissingMyDataReplicaApiEndpoint:
            timer.cancel()
    monitoring_progress.clear()
