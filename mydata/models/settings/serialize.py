"""
Methods for saving / loading / retrieving settings between the
global settings singleton and the MyData.cfg file.

The global settings singleton is imported inline when needed to avoid
circular dependencies.

The method for loading settings from disk can't use the global settings
singleton, because they are called from Settings's constructor which
would cause a circular dependency, so we pass the settings as an argument
instead.
"""
# pylint: disable=import-outside-toplevel
# pylint: disable=broad-except
import traceback
import os
from configparser import ConfigParser

from ...logs import logger


def load_settings(config_path=None):
    """
    :param config_path: Path to MyData.cfg

    Sets some default values for settings fields, then loads a settings file,
    e.g. C:\\ProgramData\\Monash University\\MyData\\MyData.cfg
    or /Users/jsmith/Library/Application Support/MyData/MyData.cfg
    """
    from ...conf import settings

    settings.set_default_config()

    if config_path is None:
        config_path = settings.config_path

    if config_path is not None and os.path.exists(config_path):
        logger.info("Reading settings from: " + config_path)
        try:
            config_parser = ConfigParser()
            config_parser.read(config_path)
            load_general_settings(config_parser)
            load_filter_settings(config_parser)
            load_advanced_settings(config_parser)
            load_miscellaneous_settings(config_parser)
        except Exception:
            logger.error(traceback.format_exc())


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
        "group_prefix",
        "max_lookup_threads",
        "max_upload_retries",
        "upload_method",
        "validate_folder_structure",
        "upload_invalid_user_or_group_folders",
    ]
    for field in fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.get(config_file_section, field)
    boolean_fields = [
        "validate_folder_structure",
        "upload_invalid_user_or_group_folders",
    ]
    for field in boolean_fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.getboolean(config_file_section, field)
    # For backwards compatibility:
    if not config_parser.has_option(
        config_file_section, "upload_invalid_user_or_group_folders"
    ) and config_parser.has_option(config_file_section, "upload_invalid_user_folders"):
        settings["upload_invalid_user_or_group_folders"] = config_parser.getboolean(
            config_file_section, "upload_invalid_user_folders"
        )
    int_fields = ["max_lookup_threads", "max_upload_retries"]
    for field in int_fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.getint(config_file_section, field)


def load_miscellaneous_settings(config_parser):
    """
    :param settings: Object of class Settings to load the settings into.
    :param config_parser: The ConfigParser object which stores data read from
                          MyData.cfg

    Loads Miscellaneous settings from a ConfigParser object

    These settings don't appear in the settings dialog in the GUI version of
    MyData, i.e. they are only accessible in MyData.cfg
    """
    from ...conf import settings

    config_file_section = "MyData"
    fields = [
        "uuid",
        "cipher",
        "verification_delay",
        "cache_datafile_lookups",
        "connection_timeout",
    ]
    for field in fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.get(config_file_section, field)
    boolean_fields = ["cache_datafile_lookups"]
    for field in boolean_fields:
        if config_parser.has_option(config_file_section, field):
            settings[field] = config_parser.getboolean(config_file_section, field)
    float_fields = [
        "verification_delay",
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
            "max_lookup_threads",
            "max_upload_retries",
            "upload_method",
            "validate_folder_structure",
            "cipher",
            "uuid",
            "verification_delay",
            "cache_datafile_lookups",
            "upload_invalid_user_or_group_folders",
            "connection_timeout",
        ]
        settings_list = []
        for field in fields:
            value = settings[field]
            config_parser.set("MyData", field, str(value))
            settings_list.append(dict(key=field, value=str(value)))
        config_parser.write(config_file)
    logger.info("Saved settings to " + config_path)
