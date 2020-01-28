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
        uuid
        instrument_name
        facility_name
        data_directory
        contact_name
        contact_email
        mytardis_url
        username
        api_key
        user_filter
        dataset_filter
        experiment_filter
        folder_structure
        group_prefix
        ignore_old_datasets
        ignore_interval_number
        ignore_interval_unit
        max_upload_retries
        validate_folder_structure
        cache_datafile_lookups
        ignore_new_files
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


def test_config_get_command(set_exp_dataset_config):
    from mydata.commands.config import config_cmd

    runner = CliRunner()
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
