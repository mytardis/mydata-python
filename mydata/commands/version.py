"""
Commands for querying version number
"""
import click

from mydata.__version__ import __version__ as VERSION


@click.command()
def version():
    """
    Display version
    """
    print("MyData Command-Line Client v%s" % VERSION)
