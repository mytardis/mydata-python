"""
mydata/indexing/settings.py
"""
import os
import sys

import click
import requests

from dotenv import load_dotenv
from requests.exceptions import HTTPError

load_dotenv()


def default_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "ApiKey %s:%s"
        % (os.getenv("MYTARDIS_USERNAME"), os.getenv("MYTARDIS_API_KEY")),
    }


def validate_settings():
    """
    Check settings required for indexing
    """
    msg = ""

    if not os.getenv("MYTARDIS_URL"):
        msg += "Set a MyTardis URL with MYTARDIS_URL\n"
    if not os.getenv("MYTARDIS_USERNAME"):
        msg += "Set a MyTardis username with MYTARDIS_USERNAME\n"
    if not os.getenv("MYTARDIS_API_KEY"):
        msg += "Set a MyTardis API key with MYTARDIS_API_KEY\n"
    if not os.getenv("MYTARDIS_EXP_ID"):
        msg += "Set a MyTardis experiment ID with MYTARDIS_EXP_ID\n"
    if not os.getenv("MYTARDIS_STORAGE_BOX_NAME"):
        msg += "Set a MyTardis storage box name with MYTARDIS_STORAGE_BOX_NAME\n"
    if not os.getenv("MYTARDIS_STORAGE_BOX_PATH"):
        msg += "Set a MyTardis storage box path with MYTARDIS_STORAGE_BOX_PATH\n"
    if not os.getenv("MYTARDIS_SRC_PATH"):
        msg += "Set a data source path with MYTARDIS_SRC_PATH\n"

    if msg:
        msg = "Missing parameter(s):\n" + msg.strip()
        click.echo(msg)
        sys.exit(1)

    try:
        check_credentials()
    except (HTTPError, AssertionError):
        click.echo("MyTardis URL or credentials are invalid")
        sys.exit(1)

    click.echo("Validated MyTardis settings.\n")


def check_credentials():
    """
    Check MyTardis credentials supplied in environment variables
    """
    response = requests.get(
        "%s/api/v1/user/?format=json&username=%s"
        % (os.getenv("MYTARDIS_URL"), os.getenv("MYTARDIS_USERNAME")),
        headers=default_headers(),
    )
    response.raise_for_status()
    assert response.json()["meta"]["total_count"] == 1


def check_folder_locations(folders):
    """
    Check that folders requested for indexing are in the right location
    """
    for folder in folders:
        folder_location = os.path.dirname(os.path.realpath(folder))
        if not os.path.samefile(
            os.getenv("MYTARDIS_STORAGE_BOX_PATH"), folder_location
        ):
            click.echo(
                "Folder is not in %s/: %s"
                % (os.getenv("MYTARDIS_STORAGE_BOX_PATH"), folder)
            )
            sys.exit(1)
