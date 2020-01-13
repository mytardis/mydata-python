#!/usr/bin/env python
"""
client.py
"""
import click

from mydata.commands.config import config_cmd
from mydata.commands.scan import scan_cmd
from mydata.commands.upload import upload_cmd
from mydata.commands.version import version_cmd


@click.group()
def entry_point():
    """
    A command-line tool for uploading data to MyTardis, supporting the
    MyData configuration file format used by the MyData desktop application
    """


def run():
    """
    Main function for command-line interface.
    """

    entry_point.add_command(config_cmd)
    entry_point.add_command(scan_cmd)
    entry_point.add_command(upload_cmd)
    entry_point.add_command(version_cmd)

    entry_point()


if __name__ == "__main__":
    run()
