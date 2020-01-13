"""
Commands for querying settings in MyData.cfg
"""
from configparser import ConfigParser

import click

from mydata.conf import settings

SECTION = "MyData"


@click.group(name="config")
def config_cmd():
    """
    Query or update settings in MyData.cfg
    """


@config_cmd.command()
def discover():
    """
    Display location of MyData.cfg
    """
    print(settings.config_path)


@config_cmd.command(name="list")
def list_command():
    """
    List keys in MyData.cfg
    """
    parser = ConfigParser()
    parser.read(settings.config_path)
    for key in parser[SECTION]:
        print(key)


@config_cmd.command()
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


@config_cmd.command(name="set")
@click.argument("key")
@click.argument("value")
def set_command(key, value):
    """
    Set value in MyData.cfg
    """
    parser = ConfigParser()
    parser.read(settings.config_path)
    parser[SECTION][key] = value
    with open(settings.config_path, "w") as configfile:
        parser.write(configfile)
