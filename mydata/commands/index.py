"""
Commands for indexing data
"""
import os

import click

from ..indexing.settings import validate_settings
from ..indexing.settings import check_folder_locations
from ..tasks.indexing import scan_folder_and_upload


@click.command(name="index")
@click.argument(
    "dirs",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, readable=True, resolve_path=True
    ),
    nargs=-1,
    required=True,
)
def index_cmd(dirs):
    """
    Index data which is already in its permanent location.

    This command requires some environment variables to be set, which can be
    listed in a .env file in the current directory.  See the dotenv.example
    file included in the mydata-python repository for an example.
    """
    if os.getenv("MYTARDIS_STORAGE_BOX_PATH"):
        print()
        print("MYTARDIS_STORAGE_BOX_PATH: %s" % os.getenv("MYTARDIS_STORAGE_BOX_PATH"))
        print()

    validate_settings()
    check_folder_locations(dirs)

    for folder in dirs:
        folder = os.path.basename(folder)
        click.echo("Indexing folder: %s\n" % folder)
        scan_folder_and_upload(folder)
