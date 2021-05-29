"""
mydata/tasks/indexing.py

This module provides the scan_folder_and_upload function which is called
by mydata.commands.index.index_cmd to index files in a specified folder.

Unlike the Multipart POST and SCP via Staging upload methods, the indexing
doesn't use the settings in MyData.cfg.  Instead it expects its required
settings to provided as environment variables or in a .env file.
"""
import json
import mimetypes
import os
import re
import subprocess
import sys

from urllib.parse import quote

from ..utils.retries import requests_retry_session
from ..indexing.models.lookup import Lookup, LookupStatus
from ..indexing.models.datafile import DataFileCreation, DataFileCreationStatus

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "ApiKey %s:%s"
    % (os.getenv("MYTARDIS_USERNAME"), os.getenv("MYTARDIS_API_KEY")),
}


def lookup_or_create_dataset(dataset_folder_name):
    """Lookup or create dataset and return Dataset ID.
    """
    ds_lookup_url = (
        "%s/api/v1/dataset/?format=json&experiments__id=%s&description=%s"
        % (
            os.getenv("MYTARDIS_URL"),
            os.getenv("MYTARDIS_EXP_ID"),
            quote(dataset_folder_name),
        )
    )
    response = requests_retry_session().get(ds_lookup_url, headers=HEADERS)
    response.raise_for_status()
    datasets = response.json()
    assert datasets["meta"]["total_count"] <= 1
    if datasets["meta"]["total_count"] == 1:
        dataset_id = datasets["objects"][0]["id"]
        print(
            "Found dataset for '%s' folder with dataset_id: %s\n"
            % (dataset_folder_name, dataset_id)
        )
        return dataset_id
    dataset_dict = {
        "description": dataset_folder_name,
        "experiments": ["/api/v1/experiment/%s/" % os.getenv("MYTARDIS_EXP_ID")],
    }
    response = requests_retry_session().post(
        "%s/api/v1/dataset/" % os.getenv("MYTARDIS_URL"),
        data=json.dumps(dataset_dict),
        headers=HEADERS,
    )
    response.raise_for_status()
    dataset_id = response.json()["id"]
    print(
        "Created Dataset record for '%s' with ID: %s\n"
        % (dataset_folder_name, dataset_id)
    )
    return dataset_id


def lookup_datafile(dataset_id, filename, directory):
    """Query MyTardis API for a matching DataFile record.
    """
    df_lookup_url = (
        "%s/api/v1/dataset_file/?format=json&dataset__id=%s&filename=%s&directory=%s"
        % (os.getenv("MYTARDIS_URL"), dataset_id, quote(filename), quote(directory),)
    )
    response = requests_retry_session().get(df_lookup_url, headers=HEADERS)
    if not response.ok:
        return Lookup(dataset_id, directory, filename, LookupStatus.FAILED)
    datafiles_dict = response.json()
    # Expect 0 or 1 matches:
    matches = datafiles_dict["meta"]["total_count"]
    if not matches:
        return Lookup(dataset_id, directory, filename, LookupStatus.NOT_FOUND)
    dfos = datafiles_dict["objects"][0]["replicas"]
    if not dfos:
        return Lookup(
            dataset_id, directory, filename, LookupStatus.FOUND_UNVERIFIED_NO_DFOS
        )
    verified = any(dfo["verified"] for dfo in dfos)
    if verified:
        return Lookup(dataset_id, directory, filename, LookupStatus.FOUND_VERIFIED)
    return Lookup(dataset_id, directory, filename, LookupStatus.FOUND_UNVERIFIED)


def create_datafile(dataset_id, filename, directory, filepath, uri):
    """Create DataFile record via MyTardis API.
    """
    size = os.path.getsize(filepath)
    print("size: %s" % size)
    mimetype = mimetypes.guess_type(filepath, strict=False)[0]
    if not mimetype:
        mimetype = "application/octet-stream"
    print("mimetype: %s" % mimetype)
    md5sum = calculate_md5sum(filepath)
    print("md5sum: %s" % md5sum)
    print()

    datafile_post_data = {
        "dataset": "/api/v1/dataset/%s/" % dataset_id,
        "filename": filename,
        "directory": directory,
        "md5sum": md5sum,
        "size": size,
        "mimetype": mimetype,
        "replicas": [
            {
                "url": uri,
                "location": os.getenv("MYTARDIS_STORAGE_BOX_NAME"),
                "protocol": "file",
            }
        ],
    }

    response = requests_retry_session().post(
        "%s/api/v1/dataset_file/" % os.getenv("MYTARDIS_URL"),
        data=json.dumps(datafile_post_data),
        headers=HEADERS,
    )
    resource_uri = None
    if response.ok:
        resource_uri = response.headers["Location"]
        return DataFileCreation(
            dataset_id,
            directory,
            filename,
            resource_uri,
            DataFileCreationStatus.COMPLETED,
        )
    return DataFileCreation(
        dataset_id, directory, filename, resource_uri, DataFileCreationStatus.FAILED
    )


def scan_folder_and_upload(
    dataset_folder_name, lookup_callback, datafile_creation_callback
):
    """Scan folder, create a Dataset record for it, and create DataFile records for its files.

    lookup_callback should be a function which will be called after each
    DataFile lookup.

    datafile_creation_callback should be a function which will be called after each
    DataFile creation.
    """
    dataset_id = lookup_or_create_dataset(dataset_folder_name)
    dataset_root_dir = "%s/%s/" % (
        os.getenv("MYTARDIS_STORAGE_BOX_PATH"),
        dataset_folder_name,
    )
    for dirname, _, files in os.walk(dataset_root_dir):
        relpath = os.path.relpath(dirname, os.getenv("MYTARDIS_STORAGE_BOX_PATH"))
        for filename in sorted(files):
            uri = os.path.join(relpath, filename)
            filepath = os.path.join(os.getenv("MYTARDIS_SRC_PATH"), uri)
            print("File path: %s" % filepath)
            directory = os.path.relpath(dirname, dataset_root_dir)
            if directory == ".":
                directory = ""

            lookup = lookup_datafile(dataset_id, filename, directory)
            if lookup.status == LookupStatus.FAILED:
                print(
                    "Failed to check for existing DataFile record on MyTardis.  Skipping for now."
                )
                print()
                lookup_callback(lookup)
                continue
            if lookup.status in (
                LookupStatus.FOUND_VERIFIED,
                LookupStatus.FOUND_UNVERIFIED,
            ):
                print(
                    "DataFile record was found, so we won't create another record for this file."
                )
                print()
                lookup_callback(lookup)
                continue
            assert lookup.status in (
                LookupStatus.NOT_FOUND,
                LookupStatus.FOUND_UNVERIFIED_NO_DFOS,
            )
            lookup_callback(lookup)

            datafile_creation = create_datafile(
                dataset_id, filename, directory, filepath, uri
            )
            if datafile_creation.status == DataFileCreationStatus.FAILED:
                print("Failed to create DataFile record.  Skipping for now.")
                print()
                datafile_creation_callback(datafile_creation)
                continue

            print("Created DataFile record: %s" % datafile_creation.resource_uri)
            print()
            print()
            datafile_creation_callback(datafile_creation)


def calculate_md5sum(filepath):
    """
    Calculate MD5 sum for filepath
    """
    md5sum_binary = ["md5sum"]
    if sys.platform == "darwin":
        md5sum_binary = ["md5", "-r"]
    with subprocess.Popen(
        [*md5sum_binary, filepath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ) as proc:
        stdout, _ = proc.communicate()
    return re.match(r"\w+", stdout.decode()).group(0)
