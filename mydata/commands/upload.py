"""
Commands for uploading data
"""
import click

from mydata.commands.scan import scan, display_scan_summary
from mydata.tasks.uploads import upload_folder
from mydata.conf import settings
from mydata.models.lookup import LookupStatus
from mydata.models.upload import UploadMethod, UploadStatus, UPLOAD_STATUS


def display_verbose_upload_summary(lookups, uploads, verbosity):
    """Display extra information when running uploads with verbose option
    """
    if lookups["failed"]:
        click.echo("\nFailed lookups:")
        for lookup in lookups["failed"]:
            click.echo(lookup.filename)

    if lookups["unverified"]:
        click.echo("\nUnverified lookups:")
        for lookup in lookups["unverified"]:
            click.echo(lookup.filename)

    if verbosity >= 2:

        if lookups["not_found"]:
            click.echo("\nNot found on MyTardis server:")
            for lookup in lookups["not_found"]:
                click.echo(lookup.filename)

    if uploads["failed"]:
        click.echo("\nFailed uploads:")
        for upload in uploads["failed"]:
            click.echo("%s [%s]" % (upload.filename, upload.message))

    if uploads["completed"]:
        click.echo("\nFiles uploaded:")
        for upload in uploads["completed"]:
            click.echo("%s [%s]" % (upload.filename, UPLOAD_STATUS[upload.status]))

    click.echo("")


@click.command(name="upload")
@click.option("-v", "--verbose", count=True)
def upload_cmd(verbose):
    """
    Upload files from structure described in MyData.cfg
    """
    data_directory = "%s/" % settings.data_directory.rstrip("/")

    if verbose:
        click.echo("\nUsing MyData configuration in: %s" % settings.config_path)

    click.echo(
        '\nScanning %s using the "%s" folder structure...\n'
        % (data_directory, settings.folder_structure)
    )

    if settings.miscellaneous.cache_datafile_lookups:
        settings.initialize_verified_datafiles_cache()

    users, groups, exps, folders = scan()

    display_scan_summary(users, groups, exps, folders)

    num_files = sum([folder.num_files for folder in folders])

    lookups = dict(not_found=[], found_verified=[], unverified=[], failed=[])

    uploads = dict(completed=[], failed=[])

    def lookup_callback(lookup):
        if lookup.status == LookupStatus.NOT_FOUND:
            lookups["not_found"].append(lookup)
        elif lookup.status == LookupStatus.FOUND_VERIFIED:
            lookups["found_verified"].append(lookup)
        elif lookup.status == LookupStatus.FOUND_UNVERIFIED_UNSTAGED:
            # For now, only consider POST uploads, none of which are staged
            lookups["unverified"].append(lookup)
        elif lookup.status == LookupStatus.FAILED:
            lookups["failed"].append(lookup)

        print(
            "Looked up %s of %s files..." % (len(lookups), num_files),
            end="\r",
            flush=True,
        )

    def upload_callback(upload):
        if upload.status == UploadStatus.COMPLETED:
            uploads["completed"].append(upload)
        if upload.status == UploadStatus.FAILED:
            uploads["failed"].append(upload)

        # Only display upload progress after lookups have completed:
        if len(lookups) == num_files:
            print(
                "Uploaded %s files..." % len(uploads["completed"]), end="\r", flush=True
            )

    for folder in folders:
        upload_folder(
            folder, lookup_callback, upload_callback, UploadMethod.MULTIPART_POST
        )

    if settings.miscellaneous.cache_datafile_lookups:
        settings.save_verified_datafiles_cache()

    num_files_uploaded = sum([folder.num_files_uploaded for folder in folders])

    click.echo(
        "%s of %s files have been uploaded to MyTardis."
        % (num_files_uploaded, num_files)
    )
    num_verified = len(lookups["found_verified"])
    click.echo(
        "%s of %s files have been verified by MyTardis." % (num_verified, num_files)
    )

    click.echo(
        "%s of %s files were newly uploaded in this session."
        % (len(uploads["completed"]), num_files)
    )

    num_cache_hits = sum([folder.num_cache_hits for folder in folders])
    click.echo(
        "%s of %s file lookups were found in the local cache."
        % (num_cache_hits, num_files)
    )

    if verbose >= 1:
        display_verbose_upload_summary(lookups, uploads, verbose)
