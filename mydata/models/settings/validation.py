"""
Methods for validating settings.

The global settings singleton is imported inline to avoid
circular dependencies.
"""
# pylint: disable=import-outside-toplevel
import os
import re

from glob import glob
from datetime import datetime

import requests
from requests.exceptions import HTTPError

from ...events.stop import raise_exception_if_user_aborted
from ...logs import logger
from ...threads.flags import FLAGS
from ...utils.exceptions import InvalidSettings
from ...utils.exceptions import UserAborted
from ..facility import Facility


def validate_settings(set_status_message=None):
    """
    Validate settings (an instance of Settings)
    """
    from ...conf import settings

    dataset_count = -1

    def log_if_test_run(message):
        """
        Log message if this is a Test Run
        """
        if FLAGS.test_run_running:
            logger.testrun(message)

    try:
        raise_exception_if_user_aborted(set_status_message)
        check_for_missing_required_fields()
        log_if_test_run("Folder structure: %s"
                        % settings.advanced.folder_structure)
        warn_if_ignoring_invalid_user_folders()
        check_filters(set_status_message)
        raise_exception_if_user_aborted(set_status_message)
        if settings.advanced.validate_folder_structure:
            dataset_count = check_structure_and_count_datasets(set_status_message)
        raise_exception_if_user_aborted(set_status_message)
        check_mytardis_url(set_status_message)
        raise_exception_if_user_aborted(set_status_message)
        check_mytardis_credentials(set_status_message)
        raise_exception_if_user_aborted(set_status_message)
        check_facility(set_status_message)
        raise_exception_if_user_aborted(set_status_message)
        check_instrument(set_status_message)
        raise_exception_if_user_aborted(set_status_message)
        check_contact_email_and_email_folders(set_status_message)
        raise_exception_if_user_aborted(set_status_message)
        message = "Settings validation - succeeded!"
        logger.debug(message)
        log_if_test_run(message)
        if set_status_message:
            set_status_message(message)
        return dataset_count
    except Exception as err:
        if isinstance(err, InvalidSettings):
            raise
        if isinstance(err, UserAborted):
            raise
        message = str(err)
        logger.exception(message)
        log_if_test_run("ERROR: %s" % message)
        raise InvalidSettings(message, "")


def check_for_missing_required_fields():
    """
    Check if a required field is missing
    """
    from ...conf import settings
    if settings.general.instrument_name.strip() == "":
        message = "Please enter a valid instrument name."
        raise InvalidSettings(message, "instrument_name")
    if settings.general.data_directory.strip() == "":
        message = "Please enter a valid data directory."
        raise InvalidSettings(message, "data_directory")
    if settings.general.mytardis_url.strip() == "":
        message = "Please enter a valid MyTardis URL, " \
            "beginning with \"http://\" or \"https://\"."
        raise InvalidSettings(message, "mytardis_url")
    if settings.general.contact_name.strip() == "":
        message = "Please enter a valid contact name."
        raise InvalidSettings(message, "contact_name")
    if settings.general.contact_email.strip() == "":
        message = "Please enter a valid contact email."
        raise InvalidSettings(message, "contact_email")
    if settings.general.username.strip() == "":
        message = "Please enter a MyTardis username."
        raise InvalidSettings(message, "username")
    if settings.general.api_key.strip() == "":
        message = "Please enter your MyTardis API key.\n\n" \
            "To find your API key, log into MyTardis using the " \
            "account you wish to use with MyData (\"%s\"), " \
            "click on your username (in the upper-right corner), " \
            "and select \"Download Api Key\" from the drop-down " \
            "menu.  If \"Download Api Key\" is missing from the " \
            "drop-down menu, please contact your MyTardis " \
            "administrator.\n\n" \
            "Open the downloaded file (\"<username>.key\") in " \
            "Notepad (or a suitable text editor).  Its content "\
            "will appear as follows:\n\n" \
            "    ApiKey <username>:<API key>\n\n" \
            "Copy the <API key> (after the colon) to your clipboard," \
            " and paste it into MyData's \"MyTardis API Key\" field." \
            % settings.general.username.strip()
        raise InvalidSettings(message, "api_key")
    if not os.path.exists(settings.general.data_directory):
        message = "The data directory: \"%s\" doesn't exist!" % \
            settings.general.data_directory
        raise InvalidSettings(message, "data_directory")


def warn_if_ignoring_invalid_user_folders():
    """
    Warn if ignoring invalid user (or group) folders
    """
    from ...conf import settings

    def log_if_test_run(message):
        """
        Log message if this is a Test Run
        """
        if FLAGS.test_run_running:
            logger.testrun(message)

    if not settings.advanced.upload_invalid_user_or_group_folders:
        if settings.advanced.folder_structure.startswith("User Group"):
            message = "Invalid user group folders are being ignored."
            logger.warning(message)
            log_if_test_run("WARNING: %s" % message)
        elif "User" in settings.advanced.folder_structure or \
                "Email" in settings.advanced.folder_structure:
            message = "Invalid user folders are being ignored."
            logger.warning(message)
            log_if_test_run("WARNING: %s" % message)


def check_filters(set_status_message):
    """
    Check filter-related fields
    """
    from ...conf import settings

    def log_if_test_run(message):
        """
        Log message if this is a Test Run
        """
        if FLAGS.test_run_running:
            logger.testrun(message)

    if settings.filters.user_filter.strip() != "":
        if settings.advanced.folder_structure.startswith("User Group"):
            message = "User group folders are being filtered."
            logger.warning(message)
            log_if_test_run("WARNING: %s" % message)
        else:
            message = "User folders are being filtered."
            logger.warning(message)
            log_if_test_run("WARNING: %s" % message)
    if settings.filters.dataset_filter.strip() != "":
        message = "Dataset folders are being filtered."
        logger.warning(message)
        log_if_test_run("WARNING: %s" % message)
    if settings.filters.experiment_filter.strip() != "":
        message = "Experiment folders are being filtered."
        logger.warning(message)
        log_if_test_run("WARNING: %s" % message)
    if settings.filters.ignore_old_datasets:
        message = "Old datasets are being ignored."
        logger.warning(message)
        log_if_test_run("WARNING: %s" % message)
    if settings.filters.ignore_new_datasets:
        message = "New datasets are being ignored."
        logger.warning(message)
        log_if_test_run("WARNING: %s" % message)
    if settings.filters.ignore_new_files:
        message = "Files newer than %s minute(s) are being ignored." \
            % settings.filters.ignore_new_files_minutes
        logger.warning(message)
        log_if_test_run("WARNING: %s" % message)
    if settings.filters.use_includes_file \
            and not settings.filters.use_excludes_file:
        message = "Only files matching patterns in includes " \
            "file will be scanned for upload."
        logger.warning(message)
        log_if_test_run("WARNING: %s" % message)
    elif not settings.filters.use_includes_file \
            and settings.filters.use_excludes_file:
        message = "Files matching patterns in excludes " \
            "file will not be scanned for upload."
        logger.warning(message)
        log_if_test_run("WARNING: %s" % message)
    elif settings.filters.use_includes_file \
            and settings.filters.use_excludes_file:
        message = "Files matching patterns in excludes " \
            "file will not be scanned for upload, " \
            "unless they match patterns in the includes file."
        logger.warning(message)
        log_if_test_run("WARNING: %s" % message)
    check_datafile_glob_files(set_status_message)


def check_datafile_glob_files(set_status_message):
    """
    Check includes and excludes files
    """
    from ...conf import settings

    if settings.filters.use_includes_file:
        message = "Settings validation - checking includes file..."
        logger.debug(message)
        if set_status_message:
            set_status_message(message)
        perform_globs_file_validation(settings.filters.includes_file,
                                      "Includes", "includes", "includes_file")

    raise_exception_if_user_aborted(set_status_message)

    if settings.filters.use_excludes_file:
        message = "Settings validation - checking excludes file..."
        logger.debug(message)
        if set_status_message:
            set_status_message(message)
        perform_globs_file_validation(settings.filters.excludes_file,
                                      "Excludes", "excludes", "excludes_file")


def check_mytardis_url(set_status_message):
    """
    Check MyTardis URL
    """
    from ...conf import settings

    def log_if_test_run(message):
        """
        Log message if this is a Test Run
        """
        if FLAGS.test_run_running:
            logger.testrun(message)

    try:
        message = "Settings validation - checking MyTardis URL..."
        logger.debug(message)
        if set_status_message:
            set_status_message(message)
        response = requests.get(
            settings.general.mytardis_api_url,
            timeout=settings.miscellaneous.connection_timeout)
        history = response.history
        url = response.url
        if history:
            message = "MyData attempted to access MyTardis at " \
                "\"%s\", but was redirected to:" \
                "\n\n" % settings.general.mytardis_api_url
            message += "\t%s" % url
            message += "\n\n"
            message += "A redirection could be caused by any of " \
                "the following reasons:" \
                "\n\n" \
                "1. You may be required to log into a web portal " \
                "before you can access external sites." \
                "\n\n" \
                "2. You may be required to access external sites " \
                "via a proxy server.  This is not supported by " \
                "MyData at present." \
                "\n\n" \
                "3. You might not be using the preferred notation " \
                "for your MyTardis URL.  If attempting to navigate " \
                "to this URL in your web browser results in a " \
                "modified URL appearing in your browser's address " \
                "bar, but you are sure that the modified URL still " \
                "represents the MyTardis site you are trying to " \
                "access, then you should update the MyTardis URL " \
                "in your MyData settings, so that the MyTardis " \
                "server doesn't need to modify it." \
                "\n\n" \
                "4. Someone could have hijacked your MyTardis site " \
                "and could be redirecting you to a malicious site. " \
                "If you suspect this, please contact your MyTardis " \
                "administrator immediately."
            raise InvalidSettings(message, "mytardis_url")
        if response.status_code == 200:
            message = "Retrieved %s in %.3f seconds." \
                % (settings.general.mytardis_api_url,
                   response.elapsed.total_seconds())
            logger.debug(message)
            log_if_test_run(message)
        elif response.status_code < 200 or response.status_code >= 300:
            logger.debug("Received HTTP %d while trying to access "
                         "MyTardis server (%s)."
                         % (response.status_code,
                            settings.general.mytardis_url))
            message = (
                "Please enter a valid MyTardis URL.\n\n"
                "Received HTTP status code %d" % response.status_code)
            log_if_test_run("ERROR: %s" % message)
            raise InvalidSettings(message, "mytardis_url")
    except requests.exceptions.Timeout:
        message = "Attempt to connect to %s timed out after " \
            "%s seconds." % (settings.general.mytardis_api_url,
                             settings.miscellaneous.connection_timeout)
        log_if_test_run("ERROR: %s" % message)
        logger.exception(message)
        raise InvalidSettings(message, "mytardis_url")
    except requests.exceptions.InvalidSchema as err:
        message = (
            "Please enter a valid MyTardis URL, "
            "beginning with \"http://\" or \"https://\".\n\n"
            "%s" % str(err))
        log_if_test_run("ERROR: %s" % message)
        if not settings.general.mytardis_url.startswith("http"):
            suggestion = "http://" + settings.general.mytardis_url
        else:
            suggestion = None
        raise InvalidSettings(message, "mytardis_url", suggestion)
    except requests.exceptions.RequestException as err:
        logger.exception(str(err))
        message = (
            "Please enter a valid MyTardis URL.\n\n"
            "%s" % str(err))
        log_if_test_run("ERROR: %s" % message)
        raise InvalidSettings(message, "mytardis_url")


def check_mytardis_credentials(set_status_message):
    """
    Check MyTardis credentials

    Here we run an arbitrary query, to test whether
    our MyTardis credentials work OK with the API.
    """
    from ...conf import settings
    message = "Settings validation - checking MyTardis credentials..."
    logger.debug(message)
    if set_status_message:
        set_status_message(message)
    url = settings.general.mytardis_url + \
        "/api/v1/user/?format=json&username=" + settings.general.username
    response = requests.get(headers=settings.default_headers, url=url)
    if response.status_code < 200 or response.status_code >= 300:
        message = "Your MyTardis credentials are invalid.\n\n" \
            "Please check your Username and API Key."
        raise InvalidSettings(message, "username")


def check_facility(set_status_message):
    """
    Check facility
    """
    from ...conf import settings
    message = "Settings validation - checking MyTardis facility..."
    logger.debug(message)
    if set_status_message:
        set_status_message(message)
    if settings.general.facility_name.strip() == "":
        message = "Please enter a valid facility name."
        suggestion = None
        try:
            facilities = Facility.get_my_facilities()
            if len(facilities) == 1:
                suggestion = facilities[0].name
            raise InvalidSettings(message, "facility_name", suggestion)
        except Exception as err:
            if isinstance(err, InvalidSettings):
                raise
            logger.exception("Failed to look up accessible facilities")
            raise InvalidSettings(message, "facility_name")
    if settings.general.facility is None:
        facilities = Facility.get_my_facilities()
        message = "Facility \"%s\" was not found in MyTardis." \
            % settings.general.facility_name
        if facilities:
            message += "\n\n" + \
                "The facilities which user \"%s\" " \
                "has access to are:\n\n" % settings.general.username
            for facility in facilities:
                message = message + "    " + facility.name + "\n"
        else:
            message += "\n\n" + \
                "Please ask your MyTardis administrator to " \
                "ensure that the \"%s\" facility exists and that " \
                "user \"%s\" is a member of the managers group for " \
                "that facility." \
                % (settings.general.facility_name,
                   settings.general.username)
        suggestion = None
        if len(facilities) == 1:
            suggestion = facilities[0].name
        raise InvalidSettings(message, "facility_name", suggestion)


def check_instrument(set_status_message):
    """
    Check instrument
    """
    from ...conf import settings
    message = "Settings validation - checking instrument name..."
    logger.debug(message)
    if set_status_message:
        set_status_message(message)
    try:
        # Try to get the Instrument from the instrument name:
        _ = settings.general.instrument
    except HTTPError as err:
        message = str(err)
        raise InvalidSettings(message, "instrument_name")


def check_contact_email_and_email_folders(set_status_message):
    """
    Check contact email and email folders
    """
    from ...conf import settings
    message = "Settings validation - validating email address..."
    logger.debug(message)
    if set_status_message:
        set_status_message(message)

    try:
        assert re.match("[^@]+@[^@]+", settings.general.contact_email)
    except AssertionError:
        message = "Please enter a valid contact email."
        raise InvalidSettings(message, "contact_email")

    if settings.advanced.folder_structure.startswith('Email') and \
            settings.advanced.validate_folder_structure:
        data_dir = settings.general.data_directory
        folder_names = next(os.walk(data_dir))[1]
        for folder_name in folder_names:
            if not re.match("[^@]+@[^@]+", folder_name):
                message = "Folder name \"%s\" in \"%s\" is not a " \
                    "valid email address." % (folder_name, data_dir)
                raise InvalidSettings(message, "data_directory")


def perform_globs_file_validation(file_path, upper, lower, field):
    """
    Used to validate an "includes" or "excludes"
    file which is used to match file patterns,
    e.g. "*.txt"

    upper is an uppercase description of the glob file.
    lower is a lowercase description of the glob file.
    field
    """
    if file_path.strip() == "":
        message = "No %s file was specified." % lower
        raise InvalidSettings(message, field)
    if not os.path.exists(file_path):
        message = "Specified %s file doesn't exist." \
            % lower
        raise InvalidSettings(message, field)
    if not os.path.isfile(file_path):
        message = "Specified %s file path is not a file." \
            % lower
        raise InvalidSettings(message, field)
    with open(file_path, 'r') as globs_file:
        for line in globs_file.readlines():
            try:
                # Lines starting with '#' or ';' will be ignored.
                # Other non-blank lines are expected to be globs,
                # e.g. *.txt
                _ = line.strip()
            except UnicodeDecodeError:
                message = "%s file is not a valid plain text " \
                    "(UTF-8) file." % upper
                raise InvalidSettings(message, field)


def check_structure_and_count_datasets(set_status_message=None):
    """
    Counts datasets, while traversing the folder structure.  Previous versions
    of this method would alert the user about missing folders.

    The missing folder alerts have been removed, so the primary purpose of
    this method is to count datasets, although the Settings dialog checkbox
    which enables it is still called "Validate folder structure"
    """
    from ...conf import settings
    message = "Settings validation - checking folder structure..."
    logger.debug(message)
    if set_status_message:
        set_status_message(message)
    data_directory = settings.general.data_directory
    levels = len(settings.advanced.folder_structure.split('/'))
    dataset_count = -1
    folder_globs = []
    for level in range(1, levels + 1):
        folder_globs.append(folder_glob(level))
        files = glob(os.path.join(data_directory, *folder_globs))
        dirs = [item for item in files if os.path.isdir(item)]
        if level == levels:
            dataset_count = count_datasets_in_dirs(dirs)

    return dataset_count


def count_datasets_in_dirs(dirs):
    """
    :param dirs: List of absolute directory paths which could be dataset
                 folders, depending on the active dataset filter(s)
    """
    from ...conf import settings
    if settings.filters.ignore_old_datasets or \
            settings.filters.ignore_new_datasets:
        dataset_count = 0
        for folder in dirs:
            ctimestamp = os.path.getctime(folder)
            ctime = datetime.fromtimestamp(ctimestamp)
            age = datetime.now() - ctime
            if settings.filters.ignore_old_datasets:
                if settings.filters.ignore_new_datasets:
                    if age.total_seconds() <= \
                            settings.filters.ignore_old_datasets_interval_seconds \
                            and age.total_seconds() >= \
                            settings.filters.ignore_new_datasets_interval_seconds:
                        dataset_count += 1
                else:
                    if age.total_seconds() <= \
                            settings.filters.ignore_old_datasets_interval_seconds:
                        dataset_count += 1
            else:
                if settings.filters.ignore_new_datasets:
                    if age.total_seconds() >= \
                            settings.filters.ignore_new_datasets_interval_seconds:
                        dataset_count += 1
                else:
                    dataset_count += 1
    else:
        dataset_count = len(dirs)
    return dataset_count


def folder_glob(level, instrument_name='*'):
    """
    Get the glob used to restrict folders at a certain level, based on filters
    specified in settings.

    :param level: Folder level (1 for folders which are direct children of
                  settings.general.data_directory, 2 for grandchildren etc.)
    """
    from ...conf import settings
    user_or_group_glob = "*%s*" % settings.filters.user_filter
    dataset_glob = "*%s*" % settings.filters.dataset_filter
    exp_glob = "*%s*" % settings.filters.experiment_filter
    glob_dict = {
        'Dataset': [dataset_glob],
        'Username / Dataset': [user_or_group_glob, dataset_glob],
        'User Group / Dataset':
            [user_or_group_glob, dataset_glob],
        'Email / Dataset': [user_or_group_glob, dataset_glob],
        'Experiment / Dataset': [exp_glob, dataset_glob],
        'Username / Experiment / Dataset':
            [user_or_group_glob, exp_glob, dataset_glob],
        'User Group / Experiment / Dataset':
            [user_or_group_glob, exp_glob, dataset_glob],
        'Email / Experiment / Dataset':
            [user_or_group_glob, exp_glob, dataset_glob],
        'Username / "MyTardis" / Experiment / Dataset':
            [user_or_group_glob, 'MyTardis', exp_glob, dataset_glob],
        'User Group / Instrument / Full Name / Dataset':
            [user_or_group_glob, instrument_name, '*', dataset_glob]
    }
    return glob_dict[settings.advanced.folder_structure][level - 1]
