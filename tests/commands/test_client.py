"""
tests/commands/test_client.py
"""
import sys

from unittest.mock import patch

from mydata.client import run


def test_run_command(capsys):
    captured = capsys.readouterr()
    sys_exit_raised = False
    try:
        testargs = ["mydata", "--help"]
        with patch.object(sys, "argv", testargs):
            run()
    except SystemExit:
        sys_exit_raised = True

    assert sys_exit_raised
    captured = capsys.readouterr()
    assert "A command-line tool for uploading data to MyTardis" in captured.out
