"""
Commands for scanning folder structure
"""
import click

from mydata.tasks.folders import scan_folders
from mydata.conf import settings


def scan():
    """Scan folders from structure described in MyData.cfg
    """
    users = []
    groups = []
    exps = []
    folders = []

    def found_user(user):
        """Callback for when a user folder is found.

        If the user folder can't be mapped to a MyTardis user record,
        but settings.upload_invalid_user_or_group_folders is True,
        MyData will still create an object of class `mydata.models.user.User`
        but it will have a flag set indicating that a matching user was
        not found on the MyTardis server.

        :param user: The user object
        :type user: class:`mydata.models.user.User`
        """
        users.append(user)

    def found_group(group):
        """Callback for when a group folder is found.

        If the group folder can't be mapped to a MyTardis group record,
        but settings.upload_invalid_user_or_group_folders is True,
        MyData will proceed with creating the required Dataset and Experiment
        to hold the data, but it won't be able to grant access to the
        user group.  In this case, group.id will be None.

        :param group: The group object
        :type group: class:`mydata.models.group.Group`
        """
        groups.append(group)

    def found_exp(exp_folder_name):
        exps.append(exp_folder_name)

    def found_dataset(folder):
        folders.append(folder)

    scan_folders(found_user, found_group, found_exp, found_dataset)

    return users, groups, exps, folders


def display_scan_summary(users, groups, exps, folders):
    """Display summary of scan
    """
    data_directory = "%s/" % settings.data_directory.rstrip("/")

    for user in sorted(users, key=lambda user: user.email):
        not_found_msg = ""
        if user.user_not_found_in_mytardis:
            not_found_msg = (
                ' [USER "%s" WAS NOT FOUND ON THE MYTARDIS SERVER]' % user.username
            )
        click.echo("Found user folder: %s%s" % (user.user_folder_name, not_found_msg))

    for group in sorted(groups, key=lambda group: group.name):
        not_found_msg = ""
        if group.group_not_found_in_mytardis:
            not_found_msg = (
                ' [GROUP "%s" WAS NOT FOUND ON THE MYTARDIS SERVER]' % group.name
            )
        click.echo(
            "Found group folder: %s%s" % (group.group_folder_name, not_found_msg)
        )

    if (
        settings.folder_structure.startswith("Username")
        or settings.folder_structure.startswith("Email")
        or settings.folder_structure.startswith("User Group")
    ):
        click.echo("")

    click.echo("Found %s dataset folders in %s\n" % (len(folders), data_directory))

    # exps will only be populated if MyData is configured to use a folder structure
    # which includes experiment folders:
    if exps:
        click.echo("Datasets will be collected into %s experiments.\n" % len(exps))


@click.command(name="scan")
@click.option("-v", "--verbose", count=True)
def scan_cmd(verbose):
    """Scan folders from structure described in MyData.cfg
    """
    data_directory = "%s/" % settings.data_directory.rstrip("/")

    if verbose:
        click.echo("\nUsing MyData configuration in: %s" % settings.config_path)

    click.echo(
        '\nScanning %s using the "%s" folder structure...\n'
        % (data_directory, settings.folder_structure)
    )

    users, groups, exps, folders = scan()

    display_scan_summary(users, groups, exps, folders)
