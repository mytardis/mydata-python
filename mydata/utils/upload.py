"""
Upload data using SSH2 protocol library
"""
import os
import socket
from datetime import datetime
from tqdm import tqdm
from ssh2 import session, sftp

from ..conf import settings


def read_file_chunks(file_object, chunk_size):
    """
    Read data file chunk
    """
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def get_file_mode():
    """
    Remote file attributes
    """
    return sftp.LIBSSH2_SFTP_S_IRUSR | \
           sftp.LIBSSH2_SFTP_S_IWUSR | \
           sftp.LIBSSH2_SFTP_S_IRGRP | \
           sftp.LIBSSH2_SFTP_S_IROTH


def execute_command_over_ssh(ssh_session, command):
    """
    Execute command over existing SSH session
    """
    channel = ssh_session.open_session()
    channel.execute(command)
    message = []
    while True:
        size, data = channel.read()
        if len(data) != 0:
            message.append(data)
        if size == 0:
            break
    channel.close()
    channel.wait_closed()
    if len(message) != 0:
        raise Exception(" ".join(message))


def get_ssh_session(server, auth):
    """
    Open connection and return SSH session
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server)

    ssh_session = session.Session()
    ssh_session.handshake(sock)

    try:
        ssh_session.userauth_publickey_fromfile(auth[0], auth[1])
    except Exception as err:
        raise Exception("Can't open SSH key file.") from err

    return ssh_session


def upload_file_ssh(server, auth, file_path, remote_file_path, upload,
                    progress, thread_num):
    """
    Upload file using SSH, update progress status, cancel upload if requested
    """
    # pylint: disable=too-many-locals, too-many-statements
    sess = get_ssh_session(server, auth)

    try:
        execute_command_over_ssh(
            sess,
            "mkdir -m 2770 -p %s" % os.path.dirname(remote_file_path)
        )
    except Exception as err:
        raise Exception("Can't create remote folder. %s" % str(err)) from err

    file_info = os.stat(file_path)
    channel = sess.scp_send64(remote_file_path, get_file_mode(),
                              file_info.st_size, file_info.st_mtime,
                              file_info.st_atime)

    filename = os.path.relpath(file_path, settings.general.data_directory)

    if progress:
        progress_bar = tqdm(
            position=thread_num,
            total=file_info.st_size,
            desc=filename,
            unit="B",
            unit_scale=True,
            unit_divisor=1024
        )

    upload.start_time = datetime.now()

    with open(file_path, "rb") as local_file:
        for data in read_file_chunks(local_file, 32*1024*1024):
            _, bytes_written = channel.write(data)
            if progress:
                progress_bar.update(bytes_written)
            if upload.canceled:
                if progress:
                    progress_bar.close()
                break

    upload.set_latest_time(datetime.now())
    upload.bytes_uploaded = file_info.st_size

    if progress:
        progress_bar.close()

    channel.send_eof()
    channel.wait_eof()

    channel.close()
    channel.wait_closed()

    try:
        execute_command_over_ssh(sess, "chmod 660 %s" % remote_file_path)
    except Exception as err:
        raise Exception("Can't set remote file permissions. %s" % str(err)) \
            from err

    sess.disconnect()
