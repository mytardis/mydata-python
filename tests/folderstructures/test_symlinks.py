"""
Test ability to ignore symlink files
"""
import os
import requests_mock

from tests.fixtures import set_symlinks_config

from tests.mocks import (
    mock_testfacility_user_response,
    mock_test_facility_response,
    mock_test_instrument_response,
)


def test_scan_folders_with_symlink(set_symlinks_config):
    """
    Test ability to scan folder and ignore symlinks
    """
    from mydata.conf import settings
    from mydata.tasks.folders import scan_folders

    root = os.path.join(".", "tests", "testdata", "testdata-symlinks")
    src = os.path.join(root, "TestA", "test.txt")
    dst = os.path.join(root, "TestB", "symlink.txt")
    if os.path.exists(dst):
        os.remove(dst)
    os.symlink(src, dst)
    assert os.path.islink(dst)

    folders = []

    # We don't need callbacks for these in this case:
    found_exp = None
    found_user = None
    found_group = None

    def found_dataset(folder):
        folders.append(folder)

    with requests_mock.Mocker() as mocker:
        mock_testfacility_user_response(mocker, settings.general.mytardis_url)
        mock_test_facility_response(mocker, settings.general.mytardis_url)
        mock_test_instrument_response(mocker, settings.general.mytardis_url)

        scan_folders(found_user, found_group, found_exp, found_dataset)

    os.unlink(dst)

    assert sorted([folder.name for folder in folders]) == ["TestA", "TestB"]
    assert sum([folder.num_files for folder in folders]) == 2
