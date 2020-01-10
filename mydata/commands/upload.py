"""
Commands for uploading data
"""
import click


@click.command()
def upload():
    """
    Upload files from structure described in MyData.cfg

    This method is just a stub - we are implementing the "scan" command first,
    which simply scans the folder structure without uploading.
    """
    click.echo("Not implemented yet.")
