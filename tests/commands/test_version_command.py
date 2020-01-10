"""
tests/commands/test_version_command.py
"""
from click.testing import CliRunner

from mydata.commands.version import version
from mydata.__version__ import __version__ as VERSION


def test_version_command():
    runner = CliRunner()
    result = runner.invoke(version, [])
    assert result.exit_code == 0
    assert result.output == "MyData Command-Line Client v%s\n" % VERSION
