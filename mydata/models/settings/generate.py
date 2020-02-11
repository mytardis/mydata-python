""" Generate a MyData.cfg from command-line input
"""
import os
import uuid

from pathlib import Path

import click

from mydata.conf import settings
from mydata.utils.exceptions import InvalidSettings

from .serialize import save_settings_to_disk
from .validation import (
    validate_settings,
    check_mytardis_url,
    check_mytardis_credentials,
    check_facility,
    check_instrument,
    check_data_directory,
)


def generate_config():
    """Generate a MyData.cfg from command-line input
    """
    if os.path.exists(settings.config_path):
        click.echo("A config file already exists at %s" % settings.config_path)
        if not click.confirm("Are you sure you want to overwrite it?"):
            return

        filepath = Path(settings.config_path)
        filepath.rename("%s.bak" % settings.config_path)

    click.echo("")

    settings.miscellaneous.uuid = str(uuid.uuid1())

    try:
        settings.general.mytardis_url = click.prompt("MyTardis URL").strip()
        check_mytardis_url()
        settings.general.username = click.prompt("MyTardis Username").strip()
        settings.general.api_key = click.prompt("MyTardis API key").strip()
        check_mytardis_credentials()
        settings.general.facility_name = click.prompt("Facility Name").strip()
        check_facility()
        settings.general.instrument_name = click.prompt("Instrument Name").strip()
        check_instrument()
        settings.general.data_directory = click.prompt("Data Directory").strip()
        check_data_directory()
        settings.general.contact_name = click.prompt("Contact Name").strip()
        settings.general.contact_email = click.prompt("Contact Email").strip()

        validate_settings()
        save_settings_to_disk()
        click.echo("\nWrote settings to: %s" % settings.config_path)
    except InvalidSettings as err:
        click.echo("\nERROR: %s" % str(err), err=True)
    click.echo()
