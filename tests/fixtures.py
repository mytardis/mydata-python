"""
tests/fixtures.py
"""
import importlib
import os
import sys

import pytest

from .utils import unload_modules


@pytest.fixture
def set_exp_dataset_config(request):
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-exp-dataset.cfg'))
    assert 'mydata.settings' not in sys.modules

    def teardown():
        unload_modules()

    request.addfinalizer(teardown)


@pytest.fixture
def set_username_dataset_config(request):
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-username-dataset-post.cfg'))
    assert 'mydata.settings' not in sys.modules

    def teardown():
        unload_modules()

    request.addfinalizer(teardown)
