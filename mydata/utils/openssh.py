"""
Methods for using OpenSSH functionality from MyData.
On Windows, we bundle a Cygwin build of OpenSSH.
"""
# pylint: disable=broad-except
import sys
from datetime import datetime
import os
import subprocess
import re
import getpass
import threading
import time
import struct

import psutil
import six

from ..conf import settings
from ..logs import logger
from ..utils.exceptions import SshException
from ..utils.exceptions import ScpException
from ..utils.exceptions import PrivateKeyDoesNotExist

from ..subprocesses import DEFAULT_STARTUP_INFO
from ..subprocesses import DEFAULT_CREATION_FLAGS

from .progress import monitor_progress

if sys.platform.startswith("win"):
    import win32process  # pylint: disable=import-error

# Running subprocess's communicate from multiple threads can cause high CPU
# usage, so we poll each subprocess before running communicate, using a sleep
# interval of SLEEP_FACTOR * maxThreads.
SLEEP_FACTOR = 0.01

REMOTE_DIRS_CREATED = dict()


class OpenSSH():
    """
    A singleton instance of this class (called OPENSSH) is created in this
    module which contains paths to SSH binaries and quoting methods used for
    running remote commands over SSH via subprocesses.
    """
    def __init__(self):
        """
        Locate the SSH binaries on various systems. On Windows we bundle a
        Cygwin build of OpenSSH.
        """
        sixty_four_bit_python = (struct.calcsize('P') * 8 == 64)
        sixty_four_bit_operating_system = sixty_four_bit_python or \
            (sys.platform.startswith("win") and win32process.IsWow64Process())
        if "HOME" not in os.environ:
            os.environ["HOME"] = os.path.expanduser('~')
        if sixty_four_bit_operating_system:
            win_openssh_dir = r"win64\openssh-7.3p1-cygwin-2.6.0"
        else:
            win_openssh_dir = r"win32\openssh-7.3p1-cygwin-2.8.0"
        if hasattr(sys, "frozen"):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.realpath(
                os.path.join(os.path.dirname(__file__), "..", ".."))
            win_openssh_dir = os.path.join("resources", win_openssh_dir)
        if sys.platform.startswith("win"):
            base_dir = os.path.join(base_dir, win_openssh_dir)
            binary_suffix = ".exe"
            dot_ssh_dir = os.path.join(
                base_dir, "home", getpass.getuser(), ".ssh")
            if not os.path.exists(dot_ssh_dir):
                os.makedirs(dot_ssh_dir)
        else:
            base_dir = "/usr/"
            binary_suffix = ""

        bin_base_dir = os.path.join(base_dir, "bin")
        self.ssh = os.path.join(bin_base_dir, "ssh" + binary_suffix)
        self.scp = os.path.join(bin_base_dir, "scp" + binary_suffix)
        self.ssh_keygen = os.path.join(bin_base_dir, "ssh-keygen" + binary_suffix)
        self.mkdir = os.path.join(bin_base_dir, "mkdir" + binary_suffix)
        self.cat = os.path.join(bin_base_dir, "cat" + binary_suffix)

    @staticmethod
    def double_quote(string):
        """
        Return double-quoted string
        """
        return '"' + string.replace('"', r'\"') + '"'

    @staticmethod
    def double_quote_remote_path(string):
        """
        Return double-quoted remote path, escaping double quotes,
        backticks and dollar signs
        """
        path = string.replace('"', r'\"')
        path = path.replace('`', r'\\`')
        path = path.replace('$', r'\\$')
        return '"%s"' % path

    @staticmethod
    def default_ssh_options(connection_timeout):
        """
        Returns default SSH options
        """
        return [
            "-oPasswordAuthentication=no",
            "-oNoHostAuthenticationForLocalhost=yes",
            "-oStrictHostKeyChecking=no",
            "-oConnectTimeout=%s" % int(connection_timeout)
        ]


class KeyPair():
    """
    Represents an SSH key-pair, e.g. (~/.ssh/MyData, ~/.ssh/MyData.pub)
    """
    def __init__(self, private_key_path, public_key_path):
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self._public_key = None
        self._fingerprint = None
        self.key_type = None

    def read_public_key(self):
        """
        Read public key, including "ssh-rsa "
        """
        if self.public_key_path is not None and \
                os.path.exists(self.public_key_path):
            with open(self.public_key_path, "r") as pubkeyfile:
                return pubkeyfile.read()
        else:
            raise SshException("Couldn't access MyData.pub in ~/.ssh/")

    def delete(self):
        """
        Delete SSH keypair

        Only used by tests
        """
        os.remove(self.private_key_path)
        if self.public_key_path is not None:
            os.remove(self.public_key_path)

    @property
    def public_key(self):
        """
        Return public key as string
        """
        if self._public_key is None:
            self._public_key = self.read_public_key()
        return self._public_key

    def read_fingerprint_and_key_type(self):
        """
        Use "ssh-keygen -yl -f privateKeyFile" to extract the fingerprint
        and key type.  This only works if the public key file exists.
        If the public key file doesn't exist, we will generate it from
        the private key file using "ssh-keygen -y -f privateKeyFile".
        """
        if not os.path.exists(self.private_key_path):
            raise PrivateKeyDoesNotExist("Couldn't find valid private key in "
                                         "%s" % self.private_key_path)
        if self.public_key_path is None:
            self.public_key_path = self.private_key_path + ".pub"
        if not os.path.exists(self.public_key_path):
            with open(self.public_key_path, "w") as pubkeyfile:
                pubkeyfile.write(self.public_key)

        cmd_list = [
            OPENSSH.ssh_keygen, "-E", "md5", "-yl", "-f", self.private_key_path]
        logger.debug(" ".join(cmd_list))
        proc = subprocess.Popen(cmd_list,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                startupinfo=DEFAULT_STARTUP_INFO,
                                creationflags=DEFAULT_CREATION_FLAGS)
        stdout, _ = proc.communicate()
        if proc.returncode != 0:
            raise SshException(stdout.decode())

        fingerprint = None
        key_type = None
        if stdout is not None:
            ssh_keygen_out_components = stdout.split(b" ")
            if len(ssh_keygen_out_components) > 1:
                fingerprint = ssh_keygen_out_components[1]
                if fingerprint.upper().startswith(b"MD5:"):
                    fingerprint = fingerprint[4:]
            if len(ssh_keygen_out_components) > 3:
                key_type = ssh_keygen_out_components[-1]\
                    .strip().strip(b'(').strip(b')')

        if six.PY3:
            return fingerprint.decode(), key_type.decode()
        return fingerprint, key_type

    @property
    def fingerprint(self):
        """
        Return public key fingerprint
        """
        if self._fingerprint is None:
            self._fingerprint, self.key_type = self.read_fingerprint_and_key_type()
        return self._fingerprint


def find_key_pair(key_name="MyData", key_path=None):
    """
    Find an SSH key pair
    """
    if not key_path:
        key_path = get_key_pair_location()
    if os.path.exists(os.path.join(key_path, key_name)):
        with open(os.path.join(key_path, key_name)) as key_file:
            for line in key_file:
                if re.search(r"BEGIN .* PRIVATE KEY", line):
                    private_key_path = os.path.join(key_path, key_name)
                    public_key_path = os.path.join(key_path, key_name + ".pub")
                    if not os.path.exists(public_key_path):
                        public_key_path = None
                    return KeyPair(private_key_path, public_key_path)
    return None


def new_key_pair(key_name=None, key_path=None, key_comment=None):
    """
    Create an RSA key-pair in ~/.ssh/ (or in key_path if specified)
    for use with SSH and SCP.

    We use shell=True with subprocess to allow entering an empty
    passphrase into ssh-keygen.  Otherwise (at least on macOS),
    we get:
        "Saving key ""/Users/james/.ssh/MyData"" failed:
         passphrase is too short (minimum five characters)
    """
    if key_name is None:
        key_name = "MyData"
    if key_comment is None:
        key_comment = "MyData Key"
    if key_path is None:
        key_path = get_key_pair_location()
    if not os.path.exists(key_path):
        os.makedirs(key_path)

    private_key_path = os.path.join(key_path, key_name)
    public_key_path = private_key_path + ".pub"

    if sys.platform.startswith('win'):
        quoted_private_key_path = \
            OpenSSH.double_quote(get_cygwin_path(private_key_path))
    else:
        quoted_private_key_path = OpenSSH.double_quote(private_key_path)
    cmd_list = \
        [OpenSSH.double_quote(OPENSSH.ssh_keygen),
         "-f", quoted_private_key_path,
         "-N", '""',
         "-C", OpenSSH.double_quote(key_comment)]
    cmd = " ".join(cmd_list)
    logger.debug(cmd)
    proc = subprocess.Popen(cmd,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            shell=True,  # Allows empty passphrase
                            startupinfo=DEFAULT_STARTUP_INFO,
                            creationflags=DEFAULT_CREATION_FLAGS)
    stdout, _ = proc.communicate()

    if stdout is None or str(stdout).strip() == "":
        raise SshException("Received unexpected EOF from ssh-keygen.")
    if b"Your identification has been saved" in stdout:
        return KeyPair(private_key_path, public_key_path)
    if b"already exists" in stdout:
        raise SshException("Private key file \"%s\" already exists."
                           % private_key_path)
    raise SshException(stdout.decode())


def get_key_pair_location():
    r"""
    Get a suitable location for the SSH key pair.

    On Windows (on which MyData is most commonly deployed), MyData uses
    a shared config directory of C:\ProgramData\Monash University\MyData\,
    shared amongst multiple Windows users, so it makes sense to store
    MyData's SSH key-pair in this central location.  This means that the
    private key is private to the instrument PC, but not private to an
    individual user of the instrument PC.
    """
    if sys.platform.startswith("win"):
        return os.path.join(
            os.path.dirname(settings.config_path), ".ssh")
    return os.path.join(os.path.expanduser('~'), ".ssh")


def find_or_create_key_pair(key_name="MyData"):
    r"""
    Find the MyData SSH key-pair, creating it if necessary
    """
    key_path = get_key_pair_location()
    key_pair = find_key_pair(key_name=key_name, key_path=key_path)
    if not key_pair and sys.platform.startswith("win"):
        # Didn't find private key in shared config location,
        # so look in traditional ~/.ssh/ location:
        key_pair = find_key_pair(key_name=key_name)
    if not key_pair:
        key_pair = new_key_pair(
            key_name=key_name, key_path=key_path,
            key_comment="%s@%s"
            % (getpass.getuser(), settings.general.instrument_name))
    return key_pair


def upload_with_scp(
        file_path, username, private_key_path,
        host, port, remote_file_path, progress_callback,
        upload):
    """
    Upload a file to staging using SCP.

    Ignore bytes uploaded previously, because MyData is no longer
    chunking files, so with SCP, we will always upload the whole
    file.
    """
    if sys.platform.startswith("win"):
        file_path = get_cygwin_path(file_path)
        private_key_path = get_cygwin_path(private_key_path)

    upload.start_time = datetime.now()
    if progress_callback:
        progress_callback(current=0, total=upload.file_size, message="Uploading...")

    monitoring_progress = threading.Event()
    upload.startTime = datetime.now()
    monitor_progress(settings.miscellaneous.progress_poll_interval, upload,
                     upload.file_size, monitoring_progress, progress_callback)

    remote_dir = os.path.dirname(remote_file_path)
    create_remote_dir(remote_dir, username, private_key_path, host, port)

    scp_command_list = [
        OPENSSH.scp,
        "-v",
        "-P", port,
        "-i", private_key_path,
        file_path,
        "%s@%s:%s/" % (username, host,
                       remote_dir
                       .replace('`', r'\\`')
                       .replace('$', r'\\$'))]
    scp_command_list[2:2] = settings.miscellaneous.cipher_options
    scp_command_list[2:2] = OpenSSH.default_ssh_options(
        settings.miscellaneous.connection_timeout)

    scp_upload(upload, scp_command_list)

    set_remote_file_permissions(
        remote_file_path, username, private_key_path, host, port)

    upload.set_latest_time(datetime.now())
    upload.bytes_uploaded = upload.file_size
    if progress_callback:
        progress_callback(current=upload.file_size, total=upload.file_size)


def scp_upload(upload, scp_command_list):
    """
    Perfom an SCP upload using subprocess.Popen
    """
    scp_command_string = " ".join(scp_command_list)
    logger.debug(scp_command_string)
    try:
        scp_upload_process = subprocess.Popen(
            scp_command_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            startupinfo=DEFAULT_STARTUP_INFO,
            creationflags=DEFAULT_CREATION_FLAGS)
        upload.scp_upload_process_pid = scp_upload_process.pid
        wait_for_process_to_complete(scp_upload_process)
        stdout, _ = scp_upload_process.communicate()
        if scp_upload_process.returncode != 0:
            raise ScpException(
                stdout.decode(), scp_command_string, scp_upload_process.returncode)
    except (IOError, OSError) as err:
        raise ScpException(err, scp_command_string, returncode=255)


def set_remote_file_permissions(remote_file_path, username, private_key_path,
                                host, port):
    """
    Ensure that the mytardis account (via the mytardis group) has read and
    write access to the uploaded data so that it can be moved from staging into
    its permanent location.  With some older versions of OpenSSH (installed on
    the SCP server), umask settings from ~mydata/.bashrc are respected, but
    recent versions ignore ~/.bashrc, so we need to explicitly set the
    permissions.  rsync can do this (copy and set permissions) in a single
    command, so we could investigate switching from scp to rsync, but rsync is
    likely to be slower in most cases.
    """
    chmod_cmd_and_args = \
        [OPENSSH.ssh,
         "-p", port,
         "-n",
         "-c", settings.miscellaneous.cipher,
         "-i", private_key_path,
         "-l", username,
         host,
         "chmod 660 %s" % OpenSSH.double_quote_remote_path(remote_file_path)]
    chmod_cmd_and_args[1:1] = OpenSSH.default_ssh_options(
        settings.miscellaneous.connection_timeout)
    logger.debug(" ".join(chmod_cmd_and_args))
    chmod_process = \
        subprocess.Popen(chmod_cmd_and_args,
                         stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         startupinfo=DEFAULT_STARTUP_INFO,
                         creationflags=DEFAULT_CREATION_FLAGS)
    stdout, _ = chmod_process.communicate()
    if chmod_process.returncode != 0:
        raise SshException(stdout.decode(), chmod_process.returncode)


def wait_for_process_to_complete(process):
    """
    subprocess's communicate should do this automatically,
    but sometimes it polls too aggressively, putting unnecessary
    strain on CPUs (especially when done from multiple threads).
    """
    while True:
        poll = process.poll()
        if poll is not None:
            break
        time.sleep(SLEEP_FACTOR * settings.advanced.max_upload_threads)


def create_remote_dir(remote_dir, username, private_key_path, host, port):
    """
    Create a remote directory over SSH
    """
    if remote_dir not in REMOTE_DIRS_CREATED:
        mkdir_cmd_and_args = \
            [OPENSSH.ssh,
             "-p", port,
             "-n",
             "-c", settings.miscellaneous.cipher,
             "-i", private_key_path,
             "-l", username,
             host,
             "mkdir -m 2770 -p %s" % remote_dir]
        mkdir_cmd_and_args[1:1] = OpenSSH.default_ssh_options(
            settings.miscellaneous.connection_timeout)
        logger.debug(" ".join(mkdir_cmd_and_args))

        mkdir_process = \
            subprocess.Popen(mkdir_cmd_and_args,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             startupinfo=DEFAULT_STARTUP_INFO,
                             creationflags=DEFAULT_CREATION_FLAGS)
        stdout, _ = mkdir_process.communicate()
        if mkdir_process.returncode != 0:
            raise SshException(stdout.decode(), mkdir_process.returncode)
        REMOTE_DIRS_CREATED[remote_dir] = True


def get_cygwin_path(path):
    """
    Converts "C:\\path\\to\\file" to "/cygdrive/C/path/to/file".
    """
    realpath = os.path.realpath(path)
    match = re.search(r"^(\S):(.*)", realpath)
    if match:
        return "/cygdrive/" + match.groups()[0] + \
            match.groups()[1].replace("\\", "/")
    raise Exception("OpenSSH.get_cygwin_path: %s doesn't look like "
                    "a valid path." % path)


def clean_up_scp_and_ssh_processes():
    """
    SCP can leave orphaned SSH processes which need to be cleaned up.
    On Windows, we bundle our own SSH binary with MyData, so we can
    check that the absolute path of the SSH executable to be terminated
    matches MyData's SSH path.  On other platforms, we can use proc.cmdline()
    to ensure that the SSH process we're killing uses MyData's private key.
    """
    if not settings.uploader:
        return
    try:
        private_key_path = settings.uploader.sshKeyPair.private_key_path
    except AttributeError:
        # If sshKeyPair or private_key_path hasn't been defined yet,
        # then there won't be any SCP or SSH processes to kill.
        return
    for proc in psutil.process_iter():
        try:
            if proc.exe() == OPENSSH.ssh or proc.exe() == OPENSSH.scp:
                try:
                    if private_key_path in proc.cmdline() or \
                            sys.platform.startswith("win"):
                        proc.kill()
                except Exception:
                    pass
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            pass


# Singleton instance of OpenSSH class:
OPENSSH = OpenSSH()
