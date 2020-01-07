"""
mydata/tasks/folders.py
"""
# pylint: disable=bare-except
import datetime
import os
import traceback
from datetime import datetime
from glob import glob

from ..events.stop import raise_exception_if_user_aborted
from ..logs import logger
from ..models.folder import Folder
from ..models.group import Group
from ..models.user import User
from ..conf import settings
from ..utils.exceptions import InvalidFolderStructure


def scan_folders(found_user_cb, found_group_cb, found_exp_folder_cb, found_dataset_cb):
    """
    Scan dataset folders.

    Accepts callback ("cb") functions so the caller can be updated
    when a user, group, experiment or dataset folder is found.

    For users, groups and datasets, the callback function should
    accept an instance of the model object of class User, Group
    or Dataset.

    For the experiment folder callback, the callback function
    should accept a string specifying the experiment folder name.
    """
    data_dir = settings.general.data_directory
    default_owner = settings.general.default_owner
    folder_structure = settings.advanced.folder_structure
    logger.debug("FoldersModel.scan_folders(): Scanning " + data_dir + "...")
    if folder_structure.startswith("Username") or folder_structure.startswith("Email"):
        scan_for_user_folders(found_user_cb, found_exp_folder_cb, found_dataset_cb)
    elif folder_structure.startswith("User Group"):
        scan_for_group_folders(found_group_cb, found_exp_folder_cb, found_dataset_cb)
    elif folder_structure.startswith("Experiment"):
        scan_for_experiment_folders(
            found_exp_folder_cb, found_dataset_cb, data_dir, default_owner
        )
    elif folder_structure.startswith("Dataset"):
        scan_for_dataset_folders(found_dataset_cb, data_dir, default_owner)
    else:
        raise InvalidFolderStructure("Unknown folder structure.")


def scan_for_user_folders(found_user_cb, found_exp_folder_cb, found_dataset_cb):
    """
    Scan for user folders.
    """
    folder_structure = settings.advanced.folder_structure
    upload_invalid_user_or_group_folders = (
        settings.advanced.upload_invalid_user_or_group_folders
    )
    for user_folder_name in user_folder_names(settings.general.data_directory):
        raise_exception_if_user_aborted()
        logger.debug(
            "Found folder assumed to be %s: %s" % (user_folder_type(), user_folder_name)
        )
        user = User.get_user_for_folder(user_folder_name.strip())
        raise_exception_if_user_aborted()
        if not user:
            message = "Didn't find a MyTardis user record for folder " '"%s" in %s' % (
                user_folder_name,
                settings.general.data_directory,
            )
            logger.warning(message)
            if not upload_invalid_user_or_group_folders:
                logger.warning(
                    "Skipping %s, because "
                    "'Upload invalid user folders' "
                    "setting is not checked." % user_folder_name
                )
                continue
            user = User.get_user_for_folder(
                user_folder_name, user_not_found_in_mytardis=True
            )

        found_user_cb(user)

        user_folder_path = os.path.join(
            settings.general.data_directory, user_folder_name
        )
        logger.debug("Folder structure: " + folder_structure)
        if folder_structure in ("Username / Dataset", "Email / Dataset"):
            scan_for_dataset_folders(
                found_dataset_cb, user_folder_path, user, user_folder_name
            )
        elif folder_structure in (
            "Username / Experiment / Dataset",
            "Email / Experiment / Dataset",
        ):
            scan_for_experiment_folders(
                found_exp_folder_cb,
                found_dataset_cb,
                user_folder_path,
                user,
                user_folder_name,
            )
        elif folder_structure == 'Username / "MyTardis" / Experiment / Dataset':
            user_folder_contents = os.listdir(user_folder_path)
            mytardis_folder_name = None
            for item in user_folder_contents:
                if item.lower() == "mytardis":
                    mytardis_folder_name = item
            if not mytardis_folder_name:
                message = 'Didn\'t find "MyTardis" folder in ' '"%s"' % user_folder_path
                logger.warning(message)
                continue
            mytardis_folder_path = os.path.join(user_folder_path, mytardis_folder_name)
            scan_for_experiment_folders(
                found_exp_folder_cb,
                found_dataset_cb,
                mytardis_folder_path,
                user,
                user_folder_name,
            )
        raise_exception_if_user_aborted()


def scan_for_group_folders(found_group_cb, found_exp_folder_cb, found_dataset_cb):
    """
    Scan for group folders.
    """
    folder_structure = settings.advanced.folder_structure
    upload_invalid_user_or_group_folders = (
        settings.advanced.upload_invalid_user_or_group_folders
    )
    for group_folder_name in group_folder_names(settings.general.data_directory):
        raise_exception_if_user_aborted()
        logger.debug("Found folder assumed to be user group name: " + group_folder_name)
        group_name = settings.advanced.group_prefix + group_folder_name
        group = Group.get_group_by_name(group_name)
        if not group:
            message = (
                "Didn't find a MyTardis user group record for "
                'folder "%s" in %s'
                % (group_folder_name, settings.general.data_directory)
            )
            logger.warning(message)
            if not upload_invalid_user_or_group_folders:
                logger.warning(
                    "Skipping %s, because "
                    "'Upload invalid user group folders' "
                    "setting is not checked." % group_folder_name
                )
                continue
        raise_exception_if_user_aborted()
        group_folder_path = os.path.join(
            settings.general.data_directory, group_folder_name
        )
        default_owner = settings.general.default_owner
        if folder_structure == "User Group / Instrument / Full Name / Dataset":
            import_group_folders(found_dataset_cb, group_folder_path, group)
        elif folder_structure == "User Group / Experiment / Dataset":
            scan_for_experiment_folders(
                found_exp_folder_cb,
                found_dataset_cb,
                group_folder_path,
                default_owner,
                group=group,
                group_folder_name=group_folder_name,
            )
        elif folder_structure == "User Group / Dataset":
            scan_for_dataset_folders(
                found_dataset_cb,
                group_folder_path,
                owner=default_owner,
                group=group,
                group_folder_name=group_folder_name,
            )
        else:
            raise InvalidFolderStructure("Unknown folder structure.")
        raise_exception_if_user_aborted()
        found_group_cb(group)


def scan_for_dataset_folders(
    found_dataset_cb,
    path_to_scan,
    owner,
    user_folder_name=None,
    group=None,
    group_folder_name=None,
):
    """
    Scan for dataset folders.
    """
    if user_folder_name is None and group_folder_name is None:
        user_folder_name = owner.username
    try:
        logger.debug("Scanning " + path_to_scan + " for dataset folders...")
        for dataset_folder_name in dataset_folder_names(path_to_scan):
            logger.debug("Found folder assumed to be dataset: " + dataset_folder_name)
            if settings.filters.ignore_old_datasets and dataset_is_too_old(
                path_to_scan, dataset_folder_name
            ):
                continue
            if settings.filters.ignore_new_datasets and dataset_is_too_new(
                path_to_scan, dataset_folder_name
            ):
                continue
            folder = Folder(
                name=dataset_folder_name,
                location=path_to_scan,
                user_folder_name=user_folder_name,
                group_folder_name=group_folder_name,
                owner=owner,
                group=group,
            )
            raise_exception_if_user_aborted()
            folder.set_created_date()
            set_experiment_title(folder, owner, group_folder_name)
            found_dataset_cb(folder)
    except:
        logger.error(traceback.format_exc())


def scan_for_experiment_folders(
    found_exp_folder_cb,
    found_dataset_cb,
    path_to_scan,
    owner,
    user_folder_name=None,
    group=None,
    group_folder_name=None,
):
    """
    Scans for experiment folders.

    The MyTardis role account specified in the Settings dialog will
    automatically be given access (and ownership) to every experiment
    created.  If the experiment folder is found within a user folder,
    then that user will be given access, and similarly, if it is
    found within a user group folder, then the user group will be
    given access.
    """
    if user_folder_name is None and group_folder_name is None:
        user_folder_name = owner.username
    folder_structure = settings.advanced.folder_structure
    for exp_folder_name in experiment_folder_names(path_to_scan):
        exp_folder_path = os.path.join(path_to_scan, exp_folder_name)
        for dataset_folder_name in dataset_folder_names(exp_folder_path):
            if settings.filters.ignore_old_datasets and dataset_is_too_old(
                exp_folder_path, dataset_folder_name
            ):
                continue
            if settings.filters.ignore_new_datasets and dataset_is_too_new(
                exp_folder_path, dataset_folder_name
            ):
                continue
            folder = Folder(
                name=dataset_folder_name,
                location=exp_folder_path,
                user_folder_name=user_folder_name,
                group_folder_name=group_folder_name,
                owner=owner,
                group=group,
            )
            raise_exception_if_user_aborted()
            if (
                folder_structure.startswith("Username")
                or folder_structure.startswith("Email")
                or folder_structure.startswith("Experiment")
            ):
                folder.experiment_title = exp_folder_name
            elif folder_structure.startswith("User Group / Experiment"):
                if group:
                    group_name = group.short_name
                else:
                    group_name = group_folder_name
                folder.experiment_title = "%s - %s" % (group_name, exp_folder_name)
            else:
                raise InvalidFolderStructure("Unknown folder structure.")
            folder.set_created_date()
            found_dataset_cb(folder)
        files_depth1 = files_in_top_level(exp_folder_path)
        if files_depth1:
            logger.info(
                "Found %s experiment file(s) in %s\n"
                % (len(files_depth1), exp_folder_path)
            )
            folder = Folder(
                name="__EXPERIMENT_FILES__",
                location=exp_folder_path,
                user_folder_name=user_folder_name,
                group_folder_name=group_folder_name,
                owner=owner,
                group=group,
                is_exp_files_folder=True,
            )
            raise_exception_if_user_aborted()
            folder.experiment_title = exp_folder_name
            folder.set_created_date()
            found_dataset_cb(folder)
        found_exp_folder_cb(exp_folder_name)


def import_group_folders(found_dataset_cb, group_folder_path, group):
    """
    Imports folders structured according to the
    "User Group / Instrument / Researcher's Name / Dataset"
    folder structure, starting with user group folders,
    e.g. D:\\Data\\Smith-Lab\\

    Rather than reading data from any folder we happen to find at
    the Instrument level, MyData uses the instrument name specified
    in MyData's Settings dialog.  That way, MyData can be run on a
    collection of data from multiple instruments, and just select
    one instrument at a time.

    For the User Group / Instrument / Researcher's Name / Dataset
    folder structure, the default owner in MyTardis will always
    by the user listed in MyData's settings dialog.  An additional
    ObjectACL will be created in MyTardis to grant access to the
    User Group.  The researcher's name in this folder structure is
    used to determine the default experiment name, but it is not
    used to determine access control.
    """
    try:
        logger.debug("Scanning " + group_folder_path + " for instrument folders...")

        instrument_folder_path = os.path.join(
            group_folder_path, settings.general.instrument_name
        )

        if not os.path.exists(instrument_folder_path):
            logger.warning("Path %s doesn't exist." % instrument_folder_path)
            return

        owner = settings.general.default_owner

        logger.debug("Scanning " + instrument_folder_path + " for user folders...")
        user_folders = next(os.walk(instrument_folder_path))[1]
        raise_exception_if_user_aborted()
        for user_folder_name in user_folders:
            user_folder_path = os.path.join(instrument_folder_path, user_folder_name)
            logger.debug("Scanning " + user_folder_path + " for dataset folders...")
            for dataset_folder_name in dataset_folder_names(user_folder_path):
                if settings.filters.ignore_old_datasets and dataset_is_too_old(
                    user_folder_path, dataset_folder_name
                ):
                    continue
                if settings.filters.ignore_new_datasets and dataset_is_too_new(
                    user_folder_path, dataset_folder_name
                ):
                    continue
                group_folder_name = os.path.basename(group_folder_path)
                folder = Folder(
                    name=dataset_folder_name,
                    location=user_folder_path,
                    user_folder_name=user_folder_name,
                    group_folder_name=group_folder_name,
                    owner=owner,
                    group=group,
                )
                raise_exception_if_user_aborted()
                folder.set_created_date()
                folder.experiment_title = "%s - %s" % (
                    settings.general.instrument_name,
                    user_folder_name,
                )
                found_dataset_cb(folder)
    except InvalidFolderStructure:
        raise
    except:
        logger.error(traceback.format_exc())


def folder_names(path_to_scan, filter_pattern=""):
    """
    List of folder names in path matching the filter pattern
    (or all folders in the specified path if there is no filter).
    """
    files_depth1 = glob(os.path.join(path_to_scan, "*%s*" % filter_pattern))
    dirs_depth1 = [item for item in files_depth1 if os.path.isdir(item)]
    return [os.path.basename(d) for d in dirs_depth1]


def user_folder_names(path_to_scan):
    """
    List of folder names in path matching user filter (or
    all folders in the specified path if there is no filter).
    """
    return folder_names(path_to_scan, settings.filters.user_filter)


def group_folder_names(path_to_scan):
    """
    List of folder names in path matching group filter (or
    all folders in the specified path if there is no filter).

    The filter field for user groups is still stored as
    SETTING.filter.user_filter even though the user interface
    (settings dialog) presents it as a "user group" filter
    when a User Group folder structure is selected.
    """
    return folder_names(path_to_scan, settings.filters.user_filter)


def dataset_folder_names(path_to_scan):
    """
    Return a list of dataset folder names in the specified
    folder path, matching the dataset filter (if one exists).
    """
    return folder_names(path_to_scan, settings.filters.dataset_filter)


def experiment_folder_names(path_to_scan):
    """
    Return a list of experiment folder names in the specified
    folder path, matching the experiment filter (if one exists).
    """
    return folder_names(path_to_scan, settings.filters.experiment_filter)


def files_in_top_level(exp_folder_path):
    """
    Return a list of file names in the specified experiment
    folder path, not within any specific dataset folder.
    """
    glob_depth1 = glob(
        os.path.join(exp_folder_path, "*%s*" % settings.filters.dataset_filter)
    )
    return [item for item in glob_depth1 if os.path.isfile(item)]


def dataset_is_too_old(path_to_scan, dataset_folder_name):
    """
    If the supplied dataset folder is too old, according to
    our filtering settings, return True and log a warning
    """
    dataset_folder_path = os.path.join(path_to_scan, dataset_folder_name)
    ctimestamp = os.path.getctime(dataset_folder_path)
    ctime = datetime.fromtimestamp(ctimestamp)
    age = datetime.now() - ctime
    if age.total_seconds() > settings.filters.ignore_old_datasets_interval_seconds:
        message = 'Ignoring "%s", because it is ' "older than %d %s" % (
            dataset_folder_path,
            settings.filters.ignore_old_datasets_interval_number,
            settings.filters.ignore_old_datasets_interval_unit,
        )
        logger.warning(message)
        return True
    return False


def dataset_is_too_new(path_to_scan, dataset_folder_name):
    """
    If the supplied dataset folder is too new, according to
    our filtering settings, return True and log a warning
    """
    dataset_folder_path = os.path.join(path_to_scan, dataset_folder_name)
    ctimestamp = os.path.getctime(dataset_folder_path)
    ctime = datetime.fromtimestamp(ctimestamp)
    age = datetime.now() - ctime
    if age.total_seconds() < settings.filters.ignore_new_datasets_interval_seconds:
        message = 'Ignoring "%s", because it is ' "newer than %d %s" % (
            dataset_folder_path,
            settings.filters.ignore_new_datasets_interval_number,
            settings.filters.ignore_new_datasets_interval_unit,
        )
        logger.warning(message)
        return True
    return False


def user_folder_type():
    """
    Return username or email, depending on the folder structure
    """
    folder_structure = settings.advanced.folder_structure
    if folder_structure.startswith("Email"):
        return "email"
    return "username"


def set_experiment_title(folder, owner, group_folder_name):
    """
    Set the folder.experiment_title for cases where
    the user hasn't explicitly specified it in a folder name
    """
    folder_structure = settings.advanced.folder_structure
    if folder_structure.startswith("User Group / Experiment"):
        experiment_title = "%s - %s" % (
            settings.general.instrument_name,
            group_folder_name,
        )
    elif folder_structure.startswith("User Group / Dataset"):
        experiment_title = group_folder_name
    elif not owner.user_not_found_in_mytardis:
        if owner.full_name.strip() != "":
            experiment_title = "%s - %s" % (
                settings.general.instrument_name,
                owner.full_name,
            )
        else:
            experiment_title = "%s - %s" % (
                settings.general.instrument_name,
                owner.username,
            )
    elif owner.full_name != User.user_not_found_string:
        experiment_title = "%s - %s (%s)" % (
            settings.general.instrument_name,
            owner.full_name,
            User.user_not_found_string,
        )
    elif owner.username != User.user_not_found_string:
        experiment_title = "%s - %s (%s)" % (
            settings.general.instrument_name,
            owner.username,
            User.user_not_found_string,
        )
    elif owner.email != User.user_not_found_string:
        experiment_title = "%s - %s (%s)" % (
            settings.general.instrument_name,
            owner.email,
            User.user_not_found_string,
        )
    else:
        experiment_title = "%s - %s" % (
            settings.general.instrument_name,
            User.user_not_found_string,
        )
    folder.experiment_title = experiment_title
