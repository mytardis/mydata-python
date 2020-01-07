#!/usr/bin/env python
"""
client.py
"""
import click

from mydata.commands.config import config
from mydata.commands.upload import upload
from mydata.commands.version import version


@click.group()
def entry_point():
    """
    Main entry point for "click" command-line interface
    """


def run():
    """
    Main function for command-line interface.
    """

    entry_point.add_command(config)
    entry_point.add_command(upload)
    entry_point.add_command(version)

    entry_point()


if __name__ == "__main__":
    run()
