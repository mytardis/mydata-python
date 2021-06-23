"""
tests/commands/test_config_generate_command.py
"""
import os
import tempfile
import textwrap

from click.testing import CliRunner

import requests_mock

from tests.mocks import (
    mock_api_endpoints_response,
    mock_testfacility_user_response,
    mock_testuser_response,
    mock_test_facility_response,
    mock_test_instrument_response,
)
from tests.utils import unload_modules


def test_config_generate_command():
    """Test mydata config generate

    Mock the MyTardis API responses required for settings validation
    """
    from mydata.commands.config import config_cmd
    from mydata.conf import settings

    with tempfile.NamedTemporaryFile() as tmpfile:
        settings.config_path = tmpfile.name

    settings.set_default_config()

    with requests_mock.Mocker() as mocker:
        inputs = dict(
            mytardis_url="http://mytardis.example.com",
            username="testuser1",
            api_key="api_key1",
            facility="Test Facility",
            instrument="Test Instrument",
            data_directory=os.path.join(
                ".", "tests", "testdata", "testdata-email-dataset"
            ),
            contact_name="Joe Bloggs",
            contact_email="Joe.Bloggs@example.com",
        )
        mock_api_endpoints_response(mocker, inputs["mytardis_url"])
        mock_testfacility_user_response(mocker, inputs["mytardis_url"])
        mock_testuser_response(mocker, settings, inputs["username"])
        mock_test_facility_response(mocker, inputs["mytardis_url"])
        mock_test_instrument_response(mocker, inputs["mytardis_url"])
        runner = CliRunner()
        stdin = "\n".join(
            [
                inputs["mytardis_url"],
                inputs["username"],
                inputs["api_key"],
                inputs["facility"],
                inputs["instrument"],
                inputs["data_directory"],
                inputs["contact_name"],
                inputs["contact_email"],
            ]
        )
        result = runner.invoke(config_cmd, ["generate"], input=stdin)
        if result.exception:
            raise result.exception
        response = textwrap.dedent(
            """
             MyTardis URL: http://mytardis.example.com
             MyTardis Username: testuser1
             MyTardis API key: api_key1
             Facility Name: Test Facility
             Instrument Name: Test Instrument
             Data Directory: %s
             Contact Name: Joe Bloggs
             Contact Email: Joe.Bloggs@example.com

             Wrote settings to: %s
       """
            % (os.path.join(".", "tests", "testdata", "testdata-email-dataset"),
               settings.config_path)
        )
        assert result.output.strip() == response.strip()

        # We need to ensure that changes to settings singleton don't propagate
        # to subsequent tests.
        # For other tests, we're doing this in tests/fixtures.py, but this
        # test doesn't use a fixture:
        unload_modules()
