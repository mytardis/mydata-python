"""
Test folder model
"""
import importlib
import os
import sys
import tempfile

import pytest

@pytest.fixture
def set_mydata_config_path():
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-username-dataset-post.cfg'))


def test_folder_model(set_mydata_config_path):
    """
    Test folder model
    """
    from mydata import settings
    settings = importlib.reload(settings)
    from mydata.models import folder
    folder = importlib.reload(folder)
    SETTINGS = settings.SETTINGS

    from mydata.models.folder import Folder
    from mydata.models.user import UserModel

    with tempfile.NamedTemporaryFile() as temp_file:
        includes_file_path = temp_file.name
    with tempfile.NamedTemporaryFile() as temp_file:
        excludes_file_path = temp_file.name

    testuser1 = UserModel(username="testuser1")
    name = "Flowers"
    location = os.path.join(SETTINGS.general.data_directory, "testuser1")
    user_folder_name = "testuser1"
    group_folder_name = None

    # Filenames:

    #  1. 1024px-Colourful_flowers.JPG
    #  2. Flowers_growing_on_the_campus_of_Cebu_City_National
    #     _Science_High_School.jpg
    #  3. Pond_Water_Hyacinth_Flowers.jpg
    #  4. existing_unverified_full_size_file.txt
    #  5. existing_unverified_incomplete_file.txt
    #  6. missing_mydata_replica_api_endpoint.txt
    #  7. existing_verified_file.txt
    #  8. zero_sized_file.txt

    # We want this test to run on Mac, Linux and Windows, but
    # Windows uses a case-insensitive filesystem, so the
    # expected results will be slightly different.

    with open(includes_file_path, 'w') as includes_file:
        includes_file.write("# Includes comment\n")
        includes_file.write("; Includes comment\n")
        includes_file.write("\n")
        includes_file.write("*.jpg\n")
        includes_file.write("zero*\n")

    with open(excludes_file_path, 'w') as excludes_file:
        excludes_file.write("# Excludes comment\n")
        excludes_file.write("; Excludes comment\n")
        excludes_file.write("\n")
        excludes_file.write(".DS_Store\n")
        excludes_file.write("*.bak\n")
        excludes_file.write("*.txt\n")
        excludes_file.write("*.JPG\n")

    SETTINGS.filters.includes_file = includes_file_path
    SETTINGS.filters.excludes_file = excludes_file_path
    assert Folder.matches_includes("image.jpg")
    assert Folder.matches_excludes("filename.bak")

    SETTINGS.filters.use_includes_file = False
    SETTINGS.filters.use_excludes_file = False
    folder = Folder(name, location, user_folder_name,
                    group_folder_name, testuser1)
    assert folder.num_files == 8

    SETTINGS.filters.use_includes_file = True
    SETTINGS.filters.use_excludes_file = True
    expected_files = [
        ('Flowers_growing_on_the_campus_of_Cebu_City_'
         'National_Science_High_School.jpg'),
        'Pond_Water_Hyacinth_Flowers.jpg',
        'zero_sized_file.txt']
    if sys.platform.startswith("win"):
        expected_files.insert(0, '1024px-Colourful_flowers.JPG')
    folder = Folder(name, location, user_folder_name,
                    group_folder_name, testuser1)
    actual_files = sorted(
        [os.path.basename(f) for f in folder.datafile_paths['files']])
    assert actual_files == expected_files

    SETTINGS.filters.use_includes_file = True
    SETTINGS.filters.use_excludes_file = False
    folder = Folder(name, location, user_folder_name,
                    group_folder_name, testuser1)
    actual_files = sorted(
        [os.path.basename(f) for f in folder.datafile_paths['files']])
    assert actual_files == expected_files

    SETTINGS.filters.use_includes_file = False
    SETTINGS.filters.use_excludes_file = True
    if sys.platform.startswith("win"):
        expected_files = []
    else:
        expected_files = [
            ('Flowers_growing_on_the_campus_of_Cebu_City_'
             'National_Science_High_School.jpg'),
            'Pond_Water_Hyacinth_Flowers.jpg'
        ]
    folder = Folder(name, location, user_folder_name,
                    group_folder_name, testuser1)
    actual_files = sorted(
        [os.path.basename(f) for f in folder.datafile_paths['files']])
    assert actual_files == expected_files

    if os.path.exists(includes_file_path):
        os.remove(includes_file_path)
    if os.path.exists(excludes_file_path):
        os.remove(excludes_file_path)
