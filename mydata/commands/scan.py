"""
Commands for scanning folder structure
"""
import click

from mydata.tasks.folders import scan_folders
from mydata.conf import settings


@click.command()
def scan():
    """
    Scan folders from structure described in MyData.cfg
    """
    users = []
    groups = []
    exps = []
    folders = []

    def found_user(user):
        users.append(user)

    def found_group(group):
        groups.append(group)

    def found_exp(exp_folder_name):
        exps.append(exp_folder_name)

    def found_dataset(folder):
        folders.append(folder)

    data_directory = "%s/" % settings.data_directory.rstrip("/")

    click.echo(
        "Scanning %s using %s folder structure...\n"
        % (data_directory, settings.folder_structure)
    )

    scan_folders(found_user, found_group, found_exp, found_dataset)

    for user in sorted(users, key=lambda user: user.email):
        click.echo("Found user: %s" % user.email)

    for group in sorted(groups, key=lambda group: group.name):
        click.echo("Found group: %s" % group.name)

    if (
        settings.folder_structure.startswith("Username")
        or settings.folder_structure.startswith("Email")
        or settings.folder_structure.startswith("User Group")
    ):
        click.echo("")

    click.echo("Found %s dataset folders in %s\n" % (len(folders), data_directory))
