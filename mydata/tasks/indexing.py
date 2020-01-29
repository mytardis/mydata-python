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

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "ApiKey %s:%s"
    % (os.getenv("MYTARDIS_USERNAME"), os.getenv("MYTARDIS_API_KEY")),
}


def lookup_or_create_dataset(dataset_folder_name):
    """Lookup or create dataset and return Dataset ID.

    Actually for now, it assumes it can be looked up.
    If not, the assertion below will fail.
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
    response.raise_for_status()
    return response.json()


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
    response.raise_for_status()
    return response


def scan_folder_and_upload(dataset_folder_name):
    """Scan folder, create a Dataset record for it, and create DataFile records for its files.
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

            datafiles_dict = lookup_datafile(dataset_id, filename, directory)
            if datafiles_dict["meta"]["total_count"]:
                print(
                    "DataFile record was found, so we won't create another record for this file."
                )
                print()
                continue

            response = create_datafile(dataset_id, filename, directory, filepath, uri)
            print("Created DataFile record: %s" % response.headers["Location"])
            print()
            print()


def calculate_md5sum(filepath):
    """
    Calculate MD5 sum for filepath
    """
    md5sum_binary = ["md5sum"]
    if sys.platform == "darwin":
        md5sum_binary = ["md5", "-r"]
    proc = subprocess.Popen(
        [*md5sum_binary, filepath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    stdout, _ = proc.communicate()
    return re.match(r"\w+", stdout.decode()).group(0)
