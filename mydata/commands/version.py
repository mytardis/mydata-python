"""
Commands for querying version number
"""
import click

from mydata.__version__ import __version__ as VERSION


@click.command(name="version")
def version_cmd():
    """
    Display version
    """
    click.echo("MyData Command-Line Client v%s" % VERSION)
