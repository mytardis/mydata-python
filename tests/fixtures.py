"""
tests/fixtures.py
"""
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


@pytest.fixture
def set_dataset_config(request):
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-dataset.cfg'))
    assert 'mydata.settings' not in sys.modules

    def teardown():
        unload_modules()

    request.addfinalizer(teardown)


@pytest.fixture
def set_user_exp_dataset_config(request):
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-user-exp-dataset.cfg'))
    assert 'mydata.settings' not in sys.modules

    def teardown():
        unload_modules()

    request.addfinalizer(teardown)


@pytest.fixture
def set_user_mytardis_exp_dataset_config(request):
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-user-mytardis-exp-dataset.cfg'))
    assert 'mydata.settings' not in sys.modules

    def teardown():
        unload_modules()

    request.addfinalizer(teardown)


@pytest.fixture
def set_email_exp_dataset_config(request):
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-email-exp-dataset.cfg'))
    assert 'mydata.settings' not in sys.modules

    def teardown():
        unload_modules()

    request.addfinalizer(teardown)


@pytest.fixture
def set_group_dataset_config(request):
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-group-dataset.cfg'))
    assert 'mydata.settings' not in sys.modules

    def teardown():
        unload_modules()

    request.addfinalizer(teardown)


@pytest.fixture
def set_group_instrument_config(request):
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-group-instrument.cfg'))
    assert 'mydata.settings' not in sys.modules

    def teardown():
        unload_modules()

    request.addfinalizer(teardown)


@pytest.fixture
def set_group_exp_dataset_config(request):
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-group-exp-dataset.cfg'))
    assert 'mydata.settings' not in sys.modules

    def teardown():
        unload_modules()

    request.addfinalizer(teardown)
