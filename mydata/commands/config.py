"""
Commands for querying settings in MyData.cfg
"""
from configparser import ConfigParser

import click

from mydata.conf import settings

SECTION = "MyData"


@click.group()
def config():
    """
    Manage runtime config options.
    """


@config.command()
def discover():
    """
    Display location of MyData.cfg
    """
    print(settings.config_path)


@config.command(name="list")
def list_command():
    """
    List keys in MyData.cfg
    """
    parser = ConfigParser()
    parser.read(settings.config_path)
    for key in parser[SECTION]:
        print(key)


@config.command()
@click.argument("key")
def get(key):
    """
    Get value from MyData.cfg
    """
    parser = ConfigParser()
    parser.read(settings.config_path)
    for cfg_key in parser[SECTION]:
        if key == cfg_key:
            click.echo(parser[SECTION][key])
            return
    raise ValueError("%s was not found in settings." % key)
