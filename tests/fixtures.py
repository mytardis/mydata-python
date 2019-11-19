"""
tests/fixtures.py
"""
import os
import shutil
import sys
import tempfile
import threading

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
def set_email_dataset_config(request):
    os.environ['MYDATA_CONFIG_PATH'] = os.path.abspath(
        os.path.join('.', 'tests', 'testdata', 'testdata-email-dataset.cfg'))
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


@pytest.fixture
def mock_scp_server():
    import select
    import socket

    from .mock_scp_server import ThreadedSshServer
    from .utils import get_ephemeral_port

    scp_port = get_ephemeral_port()

    sshd = ThreadedSshServer(("127.0.0.1", scp_port))

    def run_mock_scp_server():
        """ Run mock SCP server """
        try:
            sshd.serve_forever()
        except (IOError, OSError, socket.error, select.error):
            pass

    thread = threading.Thread(
        target=run_mock_scp_server, name="mock_scp_server_thread")
    thread.daemon = True
    thread.start()

    yield sshd

    sshd.shutdown()
    thread.join()


@pytest.fixture
def mock_key_pair():
    from mydata.utils.openssh import find_or_create_key_pair

    # The fake SSH server needs to know the public
    # key so it can authenticate the test client.
    # So we need to ensure that the MyData keypair
    # is generated before starting the fake SSH server.
    key_pair = find_or_create_key_pair("MyDataTest")

    yield key_pair

    key_pair.delete()

    unload_modules()


@pytest.fixture
def mock_staging_path():
    from mydata.utils.openssh import get_cygwin_path

    with tempfile.NamedTemporaryFile() as temp_file:
        staging_path = temp_file.name
    os.makedirs(staging_path)
    if sys.platform.startswith("win"):
        staging_path = get_cygwin_path(staging_path)
    yield staging_path
    shutil.rmtree(staging_path)
