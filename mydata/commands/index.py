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
    lookups = dict()
    for status in (
        LookupStatus.NOT_FOUND,
        LookupStatus.FOUND_VERIFIED,
        LookupStatus.FOUND_UNVERIFIED,
        LookupStatus.FOUND_UNVERIFIED_NO_DFOS,
        LookupStatus.FAILED,
    ):
        lookups[status] = []
    datafile_creations = dict()
    for status in (DataFileCreationStatus.COMPLETED, DataFileCreationStatus.FAILED):
        datafile_creations[status] = []

    def lookup_callback(lookup):
        lookups[lookup.status].append(lookup)

    def datafile_creation_callback(datafile_creation):
        datafile_creations[datafile_creation.status].append(datafile_creation)

    for folder_path in dirs:
        folder = os.path.basename(folder_path)
        click.echo("Indexing folder: %s\n" % folder)
        scan_folder_and_upload(folder, lookup_callback, datafile_creation_callback)
        num_files += sum([len(files) for r, d, files in os.walk(folder_path)])

    num_files_indexed = (
        len(lookups[LookupStatus.FOUND_VERIFIED])
        + len(lookups[LookupStatus.FOUND_UNVERIFIED])
        + len(datafile_creations[DataFileCreationStatus.COMPLETED])
    )
    click.echo(
        "%s of %s files have been indexed by MyTardis." % (num_files_indexed, num_files)
    )
    num_verified = len(lookups[LookupStatus.FOUND_VERIFIED])
    click.echo(
        "%s of %s files have been verified by MyTardis." % (num_verified, num_files)
    )

    click.echo(
        "%s of %s files were newly indexed in this session."
        % (len(datafile_creations[DataFileCreationStatus.COMPLETED]), num_files)
    )
    if lookups[LookupStatus.FOUND_UNVERIFIED_NO_DFOS]:
        click.echo("\nFile records on server without any DataFileObjects:")
        for lookup in lookups[LookupStatus.FOUND_UNVERIFIED_NO_DFOS]:
            click.echo(
                "Dataset ID: %s, Filename: %s" % (lookup.dataset_id, lookup.filename)
            )
    click.echo()
    click.echo()
