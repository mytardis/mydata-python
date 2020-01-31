"""
Commands for indexing data
"""
import os

import click

from ..indexing.settings import validate_settings
from ..indexing.settings import check_folder_locations
from ..tasks.indexing import scan_folder_and_upload
from ..indexing.models.lookup import LookupStatus
from ..indexing.models.datafile import DataFileCreationStatus


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

    num_files = 0
    lookups = dict(not_found=[], found_verified=[], unverified=[], failed=[])
    datafile_creations = dict(completed=[], failed=[])

    def lookup_callback(lookup):
        if lookup.status == LookupStatus.NOT_FOUND:
            lookups["not_found"].append(lookup)
        elif lookup.status == LookupStatus.FOUND_VERIFIED:
            lookups["found_verified"].append(lookup)
        elif lookup.status == LookupStatus.FOUND_UNVERIFIED:
            lookups["unverified"].append(lookup)
        elif lookup.status == LookupStatus.FAILED:
            lookups["failed"].append(lookup)

    def datafile_creation_callback(datafile_creation):
        if datafile_creation.status == DataFileCreationStatus.COMPLETED:
            datafile_creations["completed"].append(datafile_creation)
        elif datafile_creation.status == DataFileCreationStatus.FAILED:
            datafile_creations["failed"].append(datafile_creation)

    for folder_path in dirs:
        folder = os.path.basename(folder_path)
        click.echo("Indexing folder: %s\n" % folder)
        scan_folder_and_upload(folder, lookup_callback, datafile_creation_callback)
        num_files += sum([len(files) for r, d, files in os.walk(folder_path)])

    num_files_indexed = (
        len(lookups["found_verified"])
        + len(lookups["unverified"])
        + len(datafile_creations["completed"])
    )
    click.echo(
        "%s of %s files have been indexed by MyTardis." % (num_files_indexed, num_files)
    )
    num_verified = len(lookups["found_verified"])
    click.echo(
        "%s of %s files have been verified by MyTardis." % (num_verified, num_files)
    )

    click.echo(
        "%s of %s files were newly indexed in this session."
        % (len(datafile_creations["completed"]), num_files)
    )
    click.echo()
    click.echo()
