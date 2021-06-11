"""
Commands for uploading data
"""
import sys
import time

import click
import requests

from mydata.commands.scan import scan, display_scan_summary
from mydata.tasks.uploads import upload_folder
from mydata.conf import settings
from mydata.models.lookup import LookupStatus
from mydata.models.upload import UploadMethod, UploadStatus, UPLOAD_STATUS


def display_default_upload_summary(folders, datasets, lookups, uploads):
    """Display default summary, displayed irrespective of verbosity
    """
    num_files = sum([folder.num_files for folder in folders])
    num_files_uploaded = sum([folder.num_files_uploaded for folder in folders])

    for folder_name in sorted(datasets):
        dataset_id = datasets[folder_name]
        click.echo(
            "Data in %s/ is being archived to %s/dataset/%s"
            % (folder_name, settings.mytardis_url, dataset_id)
        )
    if datasets:
        click.echo()

    click.echo(
        "%s of %s files have been uploaded to MyTardis."
        % (num_files_uploaded, num_files)
    )
    num_verified = len(lookups["found_verified"])
    click.echo(
        "%s of %s files have been verified by MyTardis." % (num_verified, num_files)
    )

    num_unverified_no_dfos = len(lookups["unverified_no_dfos"])
    if num_unverified_no_dfos:
        click.echo(
            "%s of %s files were found unverified without any DataFileObjects! "
            "Contact server admins!" % (num_unverified_no_dfos, num_files)
        )

    click.echo(
        "%s of %s files were newly uploaded in this session."
        % (len(uploads["completed"]), num_files)
    )

    if uploads["failed"]:
        click.echo(
            "%s of %s files encountered upload errors."
            % (len(uploads["failed"]), num_files)
        )

    num_cache_hits = sum([folder.num_cache_hits for folder in folders])
    click.echo(
        "%s of %s file lookups were found in the local cache."
        % (num_cache_hits, num_files)
    )

    if lookups["unverified_no_dfos"]:
        click.echo("\nFile records on server without any DataFileObjects:")
        for lookup in lookups["unverified_no_dfos"]:
            click.echo(
                "Dataset ID: %s, Filename: %s" % (lookup.dataset_id, lookup.filename)
            )


def display_verbose_upload_summary(lookups, uploads, verbosity):
    """Display extra information when running uploads with verbose option
    """
    if lookups["failed"]:
        click.echo("\nFailed lookups:")
        for lookup in lookups["failed"]:
            click.echo("%s [%s]" % (lookup.filename, lookup.message))

    if lookups["unverified"]:
        click.echo("\nUnverified lookups:")
        for lookup in lookups["unverified"]:
            click.echo(lookup.filename)

    if verbosity >= 2:

        if lookups["not_found"]:
            click.echo("\nNot found on MyTardis server:")
            for lookup in sorted(
                lookups["not_found"], key=lambda lookup: lookup.filename
            ):
                click.echo(lookup.filename)

    if uploads["failed"]:
        click.echo("\nFailed uploads:")
        for upload in sorted(uploads["failed"], key=lambda upload: upload.filename):
            click.echo("%s [%s]" % (upload.filename, upload.message))

    if uploads["completed"]:
        click.echo("\nFiles uploaded:")
        for upload in sorted(uploads["completed"], key=lambda upload: upload.filename):
            click.echo("%s [%s]" % (upload.filename, UPLOAD_STATUS[upload.status]))

    click.echo("")


def get_approved_upload_method():
    """Check which upload method has been approved for this mydata instance
    """
    click.echo("Checking for approved upload method...\n")
    try:
        upload_via_staging_request = settings.uploader.request_staging_access()
    except requests.ConnectionError as err:
        click.echo(
            "Connection Error:  Make sure you are connected to Internet.\n", err=True
        )
        click.echo(str(err), err=True)
        sys.exit(1)
    except requests.Timeout as err:
        click.echo("Timeout Error", err=True)
        click.echo(str(err), err=True)
        sys.exit(1)
    except requests.RequestException as err:
        click.echo("General Error", err=True)
        click.echo(str(err), err=True)
        sys.exit(1)

    if upload_via_staging_request.approved:
        upload_method = UploadMethod.SCP
        click.echo("Using SCP upload method.\n")
    else:
        upload_method = UploadMethod.MULTIPART_POST
        click.echo("Using Multipart POST upload method.\n")
    return upload_method


@click.command(name="upload")
@click.option("-p", "--progress", is_flag=True)
@click.option("-v", "--verbose", count=True)
def upload_cmd(progress, verbose):
    """
    Upload files from structure described in MyData.cfg
    """
    # pylint: disable=too-many-locals, too-many-statements
    data_directory = "%s/" % settings.data_directory.rstrip("/")

    if progress and settings.advanced.upload_method != "SSH2":
        click.echo("\nTo be able to see progress bar you have to change "
                   "upload_method in config to SSH2")
        return

    if verbose:
        click.echo("\nUsing MyData configuration in: %s" % settings.config_path)

    click.echo(
        '\nScanning %s using the "%s" folder structure...\n'
        % (data_directory, settings.folder_structure)
    )

    if settings.miscellaneous.cache_datafile_lookups:
        settings.initialize_verified_datafiles_cache()

    upload_method = get_approved_upload_method()

    if upload_method == UploadMethod.MULTIPART_POST:
        if not click.confirm(
            "Uploads via staging haven't yet been approved. " "Do you want to continue?"
        ):
            sys.exit(1)
        click.echo()

    users, groups, exps, folders = scan()

    display_scan_summary(users, groups, exps, folders)

    num_files = sum([folder.num_files for folder in folders])

    lookups = dict(
        not_found=[], found_verified=[], unverified=[], unverified_no_dfos=[], failed=[]
    )

    uploads = dict(completed=[], failed=[])

    datasets = dict()

    def lookup_callback(lookup):
        if lookup.dataset_id:
            datasets[lookup.folder_name] = lookup.dataset_id
        if lookup.status == LookupStatus.NOT_FOUND:
            lookups["not_found"].append(lookup)
        elif lookup.status == LookupStatus.FOUND_VERIFIED:
            lookups["found_verified"].append(lookup)
        elif lookup.status in (
            LookupStatus.FOUND_UNVERIFIED_UNSTAGED,
            LookupStatus.FOUND_UNVERIFIED_ON_STAGING,
            LookupStatus.FOUND_UNVERIFIED_NO_DFOS,
        ):
            lookups["unverified"].append(lookup)
            if lookup.status == LookupStatus.FOUND_UNVERIFIED_NO_DFOS:
                lookups["unverified_no_dfos"].append(lookup)
        elif lookup.status == LookupStatus.FAILED:
            lookups["failed"].append(lookup)

        total_lookups = sum([len(lookups[lookup_status]) for lookup_status in lookups])

        if not uploads["completed"] and sys.stdout.isatty():
            print(
                "Looked up %s of %s files..." % (total_lookups, num_files),
                end="\r",
                flush=True,
            )

    def upload_callback(upload):
        if upload.status == UploadStatus.COMPLETED:
            uploads["completed"].append(upload)
        if upload.status == UploadStatus.FAILED:
            uploads["failed"].append(upload)

        # Only display upload progress after lookups have completed:
        if (uploads["completed"] or len(lookups) == num_files) and sys.stdout.isatty():
            print(
                "Uploaded %s of %s files...        "
                % (len(uploads["completed"]), num_files),
                end="\r",
                flush=True,
            )

    def check_lookup_completion():
        """When running in multi-threaded mode, we need to check if we have finished
        """
        total_lookups = sum([len(lookups[lookup_status]) for lookup_status in lookups])
        return total_lookups == num_files

    def check_upload_completion():
        """When running in multi-threaded mode, we need to check if we have finished
        """
        uploads_expected = (
            len(lookups[LookupStatus.NOT_FOUND])
            + len(lookups[LookupStatus.FOUND_UNVERIFIED_ON_STAGING])
            + len(lookups[LookupStatus.FOUND_UNVERIFIED_NO_DFOS])
        )
        return uploads_expected == len(uploads["completed"]) + len(uploads["failed"])

    for folder in folders:
        upload_folder(folder, lookup_callback, upload_callback,
                      progress, upload_method)

    if settings.advanced.max_lookup_threads > 1:
        while not check_lookup_completion() or not check_upload_completion():
            time.sleep(0.1)

    if settings.miscellaneous.cache_datafile_lookups:
        settings.save_verified_datafiles_cache()

    display_default_upload_summary(folders, datasets, lookups, uploads)

    if verbose >= 1:
        display_verbose_upload_summary(lookups, uploads, verbose)
