"""
Methods for saving / loading / retrieving settings between the
global settings singleton, the settings dialog, and the MyData.cfg file.

The global settings singleton is imported inline when needed to avoid
circular dependencies.

The methods for loading settings from disk and checking for updates
on the MyTardis server can't use the global settings singleton, because
they are called from Settings's constructor which would cause a
circular dependency, so we pass the settings as an argument instead.
"""
# pylint: disable=import-outside-toplevel
# pylint: disable=bare-except
import traceback
import os
import sys
from configparser import ConfigParser
from datetime import datetime

import appdirs
import requests

from ...logs import logger
from .miscellaneous import LastSettingsUpdateTrigger

OLD_DEFAULT_CONFIG_PATH = os.path.join(
    appdirs.user_data_dir("MyData", "Monash University"), "MyData.cfg"
)
if sys.platform.startswith("win"):
    NEW_DEFAULT_CONFIG_PATH = os.path.join(
        appdirs.site_config_dir("MyData", "Monash University"), "MyData.cfg"
    )
else:
    NEW_DEFAULT_CONFIG_PATH = OLD_DEFAULT_CONFIG_PATH


def load_settings(config_path=None, check_for_updates=True):
    """
    :param config_path: Path to MyData.cfg
    :param check_for_updates: Whether to look for updated settings in the
                              UploaderSettings model on the MyTardis server.

    Sets some default values for settings fields, then loads a settings file,
    e.g. C:\\ProgramData\\Monash University\\MyData\\MyData.cfg
    or /Users/jsmith/Library/Application Support/MyData/MyData.cfg
    """
    from ...conf import settings

    settings.set_default_config()

    if config_path is None:
        config_path = settings.config_path

    if (
        sys.platform.startswith("win")
        and config_path == NEW_DEFAULT_CONFIG_PATH
        and not os.path.exists(config_path)
    ):
        if os.path.exists(OLD_DEFAULT_CONFIG_PATH):
            config_path = OLD_DEFAULT_CONFIG_PATH

    if config_path is not None and os.path.exists(config_path):
        logger.info("Reading settings from: " + config_path)
        try:
            config_parser = ConfigParser()
            config_parser.read(config_path)
            load_general_settings(config_parser)
            load_filter_settings(config_parser)
            load_advanced_settings(config_parser)
            load_miscellaneous_settings(config_parser)
        except:
            logger.error(traceback.format_exc())

    if settings.miscellaneous.uuid and check_for_updates:
        if check_for_updated_settings_on_server():
            logger.debug("Updated local settings from server.")
        else:
            logger.debug("Settings were not updated from the server.")

    settings.last_settings_update_trigger = LastSettingsUpdateTrigger.READ_FROM_DISK


def load_general_settings(config_parser):
    """
    :param config_parser: The ConfigParser object which stores data read from
                         MyData.cfg

    Loads General settings from a ConfigParser object.

    These settings appear in the General tab of the settings dialog.
    """
    from ...conf import settings

    config_file_section = "MyData"
    fields = [
        "instrument_name",
        "facility_name",
        "data_directory",
        "contact_name",
        "contact_email",
        "mytardis_url",
        "username",
        "api_key",
    ]
    for field in fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.get(config_file_section, field)


def load_filter_settings(config_parser):
    """
    :param settings: Object of class Settings to load the settings into.
    :param config_parser: The ConfigParser object which stores data read from
                         MyData.cfg

    Loads Filter settings from a ConfigParser object

    These settings appear in the Filter tab of the settings dialog.
    """
    from ...conf import settings

    config_file_section = "MyData"
    fields = [
        "user_filter",
        "dataset_filter",
        "experiment_filter",
        "includes_file",
        "excludes_file",
        "ignore_interval_unit",
        "ignore_new_interval_unit",
    ]
    for field in fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.get(config_file_section, field)
    boolean_fields = [
        "ignore_old_datasets",
        "ignore_new_datasets",
        "ignore_new_files",
        "use_includes_file",
        "use_excludes_file",
    ]
    for field in boolean_fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.getboolean(config_file_section, field)
    int_fields = [
        "ignore_interval_number",
        "ignore_new_interval_number",
        "ignore_new_files_minutes",
    ]
    for field in int_fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.getint(config_file_section, field)


def load_advanced_settings(config_parser):
    """
    :param config_parser: The ConfigParser object which stores data read from
                         MyData.cfg

    Loads Advanced settings from a ConfigParser object

    These settings appear in the Advanced tab of the settings dialog.
    """
    from ...conf import settings

    config_file_section = "MyData"
    fields = [
        "folder_structure",
        "dataset_grouping",
        "group_prefix",
        "max_upload_threads",
        "max_upload_retries",
        "validate_folder_structure",
        "start_automatically_on_login",
        "upload_invalid_user_folders",
    ]
    for field in fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.get(config_file_section, field)
    boolean_fields = [
        "validate_folder_structure",
        "start_automatically_on_login",
        "upload_invalid_user_folders",
    ]
    for field in boolean_fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.getboolean(config_file_section, field)
    int_fields = ["max_upload_threads", "max_upload_retries"]
    for field in int_fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.getint(config_file_section, field)


def load_miscellaneous_settings(config_parser):
    """
    :param settings: Object of class Settings to load the settings into.
    :param config_parser: The ConfigParser object which stores data read from
                          MyData.cfg

    Loads Miscellaneous settings from a ConfigParser object

    These settings don't appear in the settings dialog, except for "locked",
    which is visible in the settings dialog, but not within any one tab view.
    """
    from ...conf import settings

    config_file_section = "MyData"
    fields = [
        "locked",
        "uuid",
        "cipher",
        "max_verification_threads",
        "verification_delay",
        "fake_md5_sum",
        "progress_poll_interval",
        "cache_datafile_lookups",
        "connection_timeout",
    ]
    for field in fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.get(config_file_section, field)
    boolean_fields = ["fake_md5_sum", "locked", "cache_datafile_lookups"]
    for field in boolean_fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.getboolean(config_file_section, field)
    int_fields = ["max_verification_threads"]
    for field in int_fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.getint(config_file_section, field)
    float_fields = [
        "verification_delay",
        "progress_poll_interval",
        "connection_timeout",
    ]
    for field in float_fields:
        if config_parser.has_option(config_file_section, field):
            try:
                settings[field] = config_parser.getfloat(config_file_section, field)
            except ValueError:
                logger.warning(
                    "Couldn't read value for %s, using default instead." % field
                )
                settings[field] = settings.miscellaneous.default[field]


def check_for_updated_settings_on_server():
    """
    Check for updated settings on server.
    """
    from ...conf import settings

    local_mod_time = datetime.fromtimestamp(os.stat(settings.config_path).st_mtime)
    try:
        settings_from_server = settings.uploader.get_settings()
        settings_updated = settings.uploader.settings_updated
    except requests.exceptions.RequestException as err:
        logger.error(err)
        settings_from_server = None
        settings_updated = datetime.fromtimestamp(0)
    if settings_from_server and settings_updated and settings_updated > local_mod_time:
        logger.debug("Settings will be updated from the server.")
        for setting in settings_from_server:
            try:
                settings[setting["key"]] = setting["value"]
                if setting["key"] in (
                    "ignore_old_datasets",
                    "ignore_new_datasets",
                    "ignore_new_files",
                    "validate_folder_structure",
                    "start_automatically_on_login",
                    "upload_invalid_user_folders",
                    "fake_md5_sum",
                    "locked",
                    "monday_checked",
                    "tuesday_checked",
                    "wednesday_checked",
                    "thursday_checked",
                    "friday_checked",
                    "saturday_checked",
                    "sunday_checked",
                    "use_includes_file",
                    "use_excludes_file",
                    "cache_datafile_lookups",
                ):
                    settings[setting["key"]] = setting["value"] == "True"
                if setting["key"] in (
                    "timer_minutes",
                    "ignore_interval_number",
                    "ignore_new_interval_number",
                    "ignore_new_files_minutes",
                    "max_verification_threads",
                    "max_upload_threads",
                    "max_upload_retries",
                ):
                    settings[setting["key"]] = int(setting["value"])
                elif setting["key"] in (
                    "progress_poll_interval",
                    "verification_delay",
                    "connection_timeout",
                ):
                    try:
                        settings[setting["key"]] = float(setting["value"])
                    except ValueError:
                        field = setting["key"]
                        logger.warning(
                            "Couldn't read value for %s, using default instead." % field
                        )
                        settings[field] = settings.miscellaneous.default[field]
            except KeyError as err:
                logger.warning(
                    "Settings field '%s' found on server is not understood "
                    "by this version of MyData." % setting["key"]
                )
        return True
    return False


def save_settings_to_disk(config_path=None):
    """
    Save configuration to disk.
    """
    from ...conf import settings

    if config_path is None:
        config_path = settings.config_path
    if config_path is None:
        raise Exception("save_settings_to_disk called " "with config_path == None.")
    config_parser = ConfigParser()
    with open(config_path, "w") as config_file:
        config_parser.add_section("MyData")
        fields = [
            "instrument_name",
            "facility_name",
            "data_directory",
            "contact_name",
            "contact_email",
            "mytardis_url",
            "username",
            "api_key",
            "user_filter",
            "dataset_filter",
            "experiment_filter",
            "includes_file",
            "excludes_file",
            "folder_structure",
            "dataset_grouping",
            "group_prefix",
            "ignore_old_datasets",
            "ignore_interval_number",
            "ignore_interval_unit",
            "ignore_new_datasets",
            "ignore_new_interval_number",
            "ignore_new_interval_unit",
            "ignore_new_files",
            "ignore_new_files_minutes",
            "use_includes_file",
            "use_excludes_file",
            "max_verification_threads",
            "max_upload_threads",
            "max_upload_retries",
            "validate_folder_structure",
            "fake_md5_sum",
            "cipher",
            "locked",
            "uuid",
            "progress_poll_interval",
            "verification_delay",
            "start_automatically_on_login",
            "cache_datafile_lookups",
            "upload_invalid_user_folders",
            "connection_timeout",
        ]
        settings_list = []
        for field in fields:
            value = settings[field]
            config_parser.set("MyData", field, str(value))
            settings_list.append(dict(key=field, value=str(value)))
        config_parser.write(config_file)
    logger.info("Saved settings to " + config_path)
    if settings.uploader:
        try:
            settings.uploader.update_settings(settings_list)
        except requests.exceptions.RequestException as err:
            logger.error(err)
