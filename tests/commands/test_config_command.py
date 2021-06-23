"""
tests/commands/test_config_command.py
"""
import textwrap

from click.testing import CliRunner

from tests.fixtures import set_exp_dataset_config


def test_config_discover_command(set_exp_dataset_config):
    from mydata.commands.config import config_cmd
    from mydata.conf import settings

    runner = CliRunner()
    result = runner.invoke(config_cmd, ["discover"])
    assert result.exit_code == 0
    assert result.output == "%s\n" % settings.config_path


def test_config_list_command(set_exp_dataset_config):
    from mydata.commands.config import config_cmd

    runner = CliRunner()
    result = runner.invoke(config_cmd, ["list"])
    assert result.exit_code == 0
    assert result.output == textwrap.dedent(
        """\
            api_key
            cache_datafile_lookups
            contact_email
            contact_name
            data_directory
            dataset_filter
            experiment_filter
            facility_name
            folder_structure
            group_prefix
            ignore_interval_number
            ignore_interval_unit
            ignore_new_files
            ignore_old_datasets
            instrument_name
            max_upload_retries
            max_upload_threads
            mytardis_url
            user_filter
            username
            uuid
            validate_folder_structure
        """
    )


def test_config_get_command(set_exp_dataset_config):
    from mydata.commands.config import config_cmd

    runner = CliRunner()
    result = runner.invoke(config_cmd, ["get", "folder_structure"])
    assert result.exit_code == 0
    assert result.output == "Experiment / Dataset\n"

    result = runner.invoke(config_cmd, ["get", "data_directory"])
    assert result.exit_code == 0
    assert result.output == "tests/testdata/testdata-exp-dataset\n"

    result = runner.invoke(config_cmd, ["get", "contact_name"])
    assert result.exit_code == 0
    assert result.output == "MyData Tester\n"

    result = runner.invoke(config_cmd, ["set", "contact_name", "Another Name"])
    assert result.exit_code == 0

    result = runner.invoke(config_cmd, ["get", "contact_name"])
    assert result.exit_code == 0
    assert result.output == "Another Name\n"

    result = runner.invoke(config_cmd, ["set", "contact_name", "MyData Tester"])
    assert result.exit_code == 0

    result = runner.invoke(config_cmd, ["get", "contact_name"])
    assert result.exit_code == 0
    assert result.output == "MyData Tester\n"
