"""
Upload data using SSH2 protocol library
"""
import os
import socket
from datetime import datetime
from tqdm import tqdm
from ssh2 import session, sftp

from ..conf import settings


def ReadFileChunks(fileObject, chunkSize):
    """
    Read data file chunk
    """
    while True:
        data = fileObject.read(chunkSize)
        if not data:
            break
        yield data


def GetFileMode():
    """
    Remote file attributes
    """
    return sftp.LIBSSH2_SFTP_S_IRUSR | \
           sftp.LIBSSH2_SFTP_S_IWUSR | \
           sftp.LIBSSH2_SFTP_S_IRGRP | \
           sftp.LIBSSH2_SFTP_S_IROTH


def ExecuteCommandOverSsh(sshSession, command):
    """
    Execute command over existing SSH session
    """
    channel = sshSession.open_session()
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


def GetSshSession(server, auth):
    """
    Open connection and return SSH session
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server)

    sshSession = session.Session()
    sshSession.handshake(sock)

    try:
        sshSession.userauth_publickey_fromfile(auth[0], auth[1])
    except:
        raise Exception("Can't open SSH key file.")

    return sshSession


def UploadFileSsh(server, auth, filePath, remoteFilePath, uploadModel):
    """
    Upload file using SSH, update progress status, cancel upload if requested
    """
    sess = GetSshSession(server, auth)

    try:
        ExecuteCommandOverSsh(
            sess,
            "mkdir -m 2770 -p %s" % os.path.dirname(remoteFilePath)
        )
    except Exception as err:
        raise Exception("Can't create remote folder. %s" % str(err))

    fileInfo = os.stat(filePath)
    channel = sess.scp_send64(remoteFilePath, GetFileMode(),
                              fileInfo.st_size, fileInfo.st_mtime,
                              fileInfo.st_atime)

    filename = os.path.relpath(filePath, settings.general.data_directory)

    progressBar = tqdm(
        total=fileInfo.st_size,
        desc=filename,
        unit="B",
        unit_scale=True,
        unit_divisor=1024
    )

    uploadModel.start_time = datetime.now()

    with open(filePath, "rb") as localFile:
        for data in ReadFileChunks(localFile, 32*1024*1024):
            _, bytesWritten = channel.write(data)
            progressBar.update(bytesWritten)
            if uploadModel.canceled:
                progressBar.close()
                break

    uploadModel.set_latest_time(datetime.now())
    uploadModel.bytes_uploaded = fileInfo.st_size

    progressBar.close()

    channel.send_eof()
    channel.wait_eof()

    channel.close()
    channel.wait_closed()

    try:
        ExecuteCommandOverSsh(sess, "chmod 660 %s" % remoteFilePath)
    except Exception as err:
        raise Exception("Can't set remote file permissions. %s" % str(err))

    sess.disconnect()
