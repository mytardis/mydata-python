"""
Commands for uploading data
"""
import click

from mydata.tasks.folders import scan_folders
from mydata.conf import settings


@click.command()
def upload():
    """
    Upload files from structure described in MyData.cfg
    """
    assert settings.folder_structure == "Experiment / Dataset"

    exps = []
    folders = []

    # We don't need callbacks for these in this case:
    found_user = None
    found_group = None

    def found_exp(exp_folder_name):
        exps.append(exp_folder_name)

    def found_dataset(folder):
        folders.append(folder)

    scan_folders(found_user, found_group, found_exp, found_dataset)
