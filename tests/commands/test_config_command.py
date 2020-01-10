"""
tests/commands/test_config_command.py
"""
import textwrap

from click.testing import CliRunner

from tests.fixtures import set_exp_dataset_config


def test_config_discover_command(set_exp_dataset_config):
    from mydata.commands.config import config
    from mydata.conf import settings

    runner = CliRunner()
    result = runner.invoke(config, ["discover"])
    assert result.exit_code == 0
    assert result.output == "%s\n" % settings.config_path


def test_config_list_command(set_exp_dataset_config):
    from mydata.commands.config import config

    runner = CliRunner()
    result = runner.invoke(config, ["list"])
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
        dataset_grouping
        group_prefix
        ignore_old_datasets
        ignore_interval_number
        ignore_interval_unit
        max_upload_threads
        max_upload_retries
        validate_folder_structure
        locked
        start_automatically_on_login
        """
    )


def test_config_get_command(set_exp_dataset_config):
    from mydata.commands.config import config

    runner = CliRunner()
    result = runner.invoke(config, ["get", "folder_structure"])
    assert result.exit_code == 0
    assert result.output == "Experiment / Dataset\n"

    result = runner.invoke(config, ["get", "data_directory"])
    assert result.exit_code == 0
    assert result.output == "tests/testdata/testdata-exp-dataset\n"
