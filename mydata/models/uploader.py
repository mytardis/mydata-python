"""
mydata/models/uploader.py

The purpose of this module is to help with registering MyData uploaders
(which are usually instrument PCs) with the MyTardis server.

MyData POSTs some basic information about the PC and about the MyData
installation to its MyTardis server.  This basic information is called an
"Uploader" record.  The Uploader is made unique by a locally-generated
UUID, so each MyData instance should only have one Uploader record in MyTardis.

Initially only HTTP POST uploads are enabled in MyData, but MyData will
request uploads via SCP to a staging area, and wait for a MyTardis
administrator to approve the request (which requires updating the
UploaderRegistrationRequest record created by MyData in the Djano Admin
interface).

The IP address information provided in the Uploader record can be used
on the SCP server to grant access via /etc/hosts.allow or equivalent.

When the MyTardis administrator approves the UploaderRegistrationRequest,
they will link the request to a MyTardis StorageBox, which must have
StorageBoxAttributes for the following keys: "scp_username", "scp_hostname".

The first time a particular scp_username and scp_hostname are used, the
MyTardis administrator needs to ensure that the "scp_username" account
has been set up properly on the staging host.  (The staging host can
be the same as the MyTardis server, or it can be another host which
mounts the same storage.)

Below is a sample of a MyTardis administrator's notes made when adding a
new scp_username ("mydata") and scp_hostname ("118.138.241.33")
to a storage box for the first time, and at the same time, adding the SSH
public key sent in the UploaderRegistrationRequest into that user's
authorized_keys file.

Ran the following as root on the staging host (118.138.241.33) :

$ adduser mydata
$ mkdir /home/mydata/.ssh
$ echo "ssh-rsa AAAAB3NzaC... MyData Key" > /home/mydata/.ssh/authorized_keys
$ chown -R mydata:mydata /home/mydata/.ssh/
$ chmod 700 /home/mydata/.ssh/
$ chmod 600 /home/mydata/.ssh/authorized_keys
$ usermod -a -G mytardis mydata

N.B.: The test below was only possible because the MyData user submitting the
request and the MyTardis administrator approving the request were the same
person.  Normally, the MyTardis administrator wouldn't have access to the
MyData user's private key.

$ ssh -i ~/.ssh/MyData mydata@118.138.241.33
[mydata@118.138.241.33 ~]$ groups
mydata mytardis
[mydata@118.138.241.33 ~]$ ls -lh /var/lib/mytardis | grep receiving
drwxrws--- 8 mytardis mytardis 4096 May 15 13:30 receiving
[mydata@118.138.241.33 ~]$ touch /var/lib/mytardis/receiving/test123.txt
[mydata@118.138.241.33 ~]$ ls -l /var/lib/mytardis/receiving/test123.txt
-rw-rw-r-- 1 mydata mytardis 0 May 15 13:40 /var/lib/mytardis/receiving/test123.txt

Note the permissions above - being part of the "mytardis" group on this staging
host allows the "mydata" user to write to the staging (receiving) directory,
but not to MyTardis's permanent storage location.

The 's' in the "receiving" directory's permissions (set with 'chmod g+s') is
important.  It means that files created within that directory by the "mydata"
user will have a default group of "mytardis" (inherited from the "receiving"
directory), instead of having a default group of "mydata".
"""
# pylint: disable=import-outside-toplevel
import json
import sys
import platform
import getpass
import re
import uuid

import urllib.parse

import psutil
import requests
import netifaces

from .. import __version__ as VERSION
from ..logs import logger
from ..utils.connectivity import get_default_interface_type
from ..utils.exceptions import (
    PrivateKeyDoesNotExist,
    NoApprovedStorageBox,
    StorageBoxOptionNotFound,
    StorageBoxAttributeNotFound,
)
from ..utils import bytes_to_human
from ..utils import mydata_install_location
from .storage import StorageBox


class Uploader:
    """
    Model class for MyTardis API v1's UploaderAppResource.
    """

    def __init__(self):
        from mydata.conf import settings

        # pylint: disable=too-many-branches
        self.uploader_id = None
        self.resource_uri = None
        self.upload_to_staging_request = None
        self.settings_updated = None
        self.ssh_key_pair = None

        self.sys_info = dict(
            osPlatform=sys.platform,
            osSystem=platform.system(),
            osRelease=platform.release(),
            osVersion=platform.version(),
            osUsername=getpass.getuser(),
            machine=platform.machine(),
            architecture=str(platform.architecture()),
            processor=platform.processor(),
            memory=bytes_to_human(psutil.virtual_memory().total),
            cpus=psutil.cpu_count(),
            hostname=platform.node(),
        )

        self.ifconfig = dict(
            interface=None, macAddress="", ipv4_addrs="", ipv6_addrs="", subnetMask=""
        )

        if settings.miscellaneous.uuid is None:
            settings.miscellaneous.uuid = str(uuid.uuid1())

        default_interface_type = get_default_interface_type()
        if default_interface_type:
            self.ifconfig["interface"] = netifaces.gateways()["default"][
                default_interface_type
            ][1]
            ifaddresses = netifaces.ifaddresses(self.ifconfig["interface"])
            if netifaces.AF_LINK in ifaddresses.keys():
                self.ifconfig["macAddress"] = ifaddresses[netifaces.AF_LINK][0]["addr"]
            if netifaces.AF_INET in ifaddresses:
                ipv4_addrs = ifaddresses[netifaces.AF_INET]
                self.ifconfig["ipv4_addrs"] = ipv4_addrs[0]["addr"]
                self.ifconfig["subnetMask"] = ipv4_addrs[0]["netmask"]
            if netifaces.AF_INET6 in ifaddresses:
                ipv6_addrs = ifaddresses[netifaces.AF_INET6]
                if sys.platform.startswith("win"):
                    self.ifconfig["ipv6_addrs"] = ipv6_addrs[0]["addr"]
                else:
                    for addr in ipv6_addrs:
                        match = re.match(r"(.+)%(.+)", addr["addr"])
                        if match and match.group(2) == self.ifconfig["interface"]:
                            self.ifconfig["ipv6_addrs"] = match.group(1)
            logger.debug(
                "The active network interface is: %s" % str(self.ifconfig["interface"])
            )
        else:
            logger.warning("There is no active network interface.")

    def upload_uploader_info(self):
        """
        Uploads info about the instrument PC to MyTardis via HTTP POST

        :raises requests.exceptions.HTTPError:
        """
        # pylint: disable=too-many-branches
        from mydata.conf import settings

        mytardis_url = settings.general.mytardis_url
        url = (
            mytardis_url
            + "/api/v1/mydata_uploader/?format=json"
            + "&uuid="
            + urllib.parse.quote(settings.miscellaneous.uuid)
        )
        response = requests.get(
            headers=settings.default_headers,
            url=url,
            timeout=settings.miscellaneous.connection_timeout,
        )
        response.raise_for_status()
        uploaders_dict = response.json()
        num_existing_uploader_records = uploaders_dict["meta"]["total_count"]
        if num_existing_uploader_records > 0:
            self.uploader_id = uploaders_dict["objects"][0]["id"]

        logger.debug("Uploading uploader info to MyTardis...")

        if num_existing_uploader_records > 0:
            url = mytardis_url + "/api/v1/mydata_uploader/%d/" % self.uploader_id
        else:
            url = mytardis_url + "/api/v1/mydata_uploader/"

        uploader_dict = {
            "uuid": settings.miscellaneous.uuid,
            "name": settings.general.instrument_name,
            "contact_name": settings.general.contact_name,
            "contact_email": settings.general.contact_email,
            "user_agent_name": "MyData",
            "user_agent_version": VERSION,
            "user_agent_install_location": mydata_install_location(),
            "os_platform": self.sys_info["osPlatform"],
            "os_system": self.sys_info["osSystem"],
            "os_release": self.sys_info["osRelease"],
            "os_version": self.sys_info["osVersion"],
            "os_username": self.sys_info["osUsername"],
            "machine": self.sys_info["machine"],
            "architecture": self.sys_info["architecture"],
            "processor": self.sys_info["processor"],
            "memory": self.sys_info["memory"],
            "cpus": self.sys_info["cpus"],
            "disk_usage": "",
            "data_path": settings.general.data_directory,
            "default_user": settings.general.username,
            "interface": self.ifconfig["interface"],
            "mac_address": self.ifconfig["macAddress"],
            "ipv4_address": self.ifconfig["ipv4_addrs"],
            "ipv6_address": self.ifconfig["ipv6_addrs"],
            "subnet_mask": self.ifconfig["subnetMask"],
            "hostname": self.sys_info["hostname"],
            "instruments": [settings.general.instrument.resource_uri],
        }

        data = json.dumps(uploader_dict, indent=4)
        logger.debug(data)
        if num_existing_uploader_records > 0:
            response = requests.put(
                headers=settings.default_headers,
                url=url,
                data=data.encode(),
                timeout=settings.miscellaneous.connection_timeout,
            )
        else:
            response = requests.post(
                headers=settings.default_headers,
                url=url,
                data=data.encode(),
                timeout=settings.miscellaneous.connection_timeout,
            )
        response.raise_for_status()
        logger.debug("Upload succeeded for uploader info.")
        self.resource_uri = response.json()["resource_uri"]

    @property
    def name(self):
        """
        For now the uploader name is the same as the instrument name, but
        that could change if we ever support uploading data from multiple
        instruments using the same MyData instance.
        """
        from mydata.conf import settings

        return settings.general.instrument_name

    @property
    def hostname(self):
        """
        Return the instrument PC's hostname
        """
        return self.sys_info["hostname"]

    def existing_upload_to_staging_request(self):
        """
        Look for existing upload to staging request.

        Ensures that a MyData SSH key-pair exists, creating one if needed.

        :raises requests.exceptions.HTTPError:
        """
        from mydata.conf import settings
        from mydata.utils.openssh import find_or_create_key_pair

        if not self.ssh_key_pair:
            self.ssh_key_pair = find_or_create_key_pair()
        mytardis_url = settings.general.mytardis_url
        url = (
            mytardis_url
            + "/api/v1/mydata_uploaderregistrationrequest/?format=json"
            + "&uploader__uuid="
            + settings.miscellaneous.uuid
            + "&requester_key_fingerprint="
            + urllib.parse.quote(self.ssh_key_pair.fingerprint)
        )
        logger.debug(url)
        headers = settings.default_headers
        response = requests.get(headers=headers, url=url)
        response.raise_for_status()
        logger.debug(response.text)
        uploaders_dict = response.json()
        if uploaders_dict["meta"]["total_count"] > 0:
            approval_dict = uploaders_dict["objects"][0]
            logger.debug("A request already exists for this uploader.")
            return UploaderRegistrationRequest(urr_dict=approval_dict)
        message = "This uploader hasn't requested uploading via staging yet."
        logger.debug(message)
        return None

    def request_upload_to_staging_approval(self):
        """
        Used to request the ability to upload via SCP
        to a staging area, and then register in MyTardis.

        :raises requests.exceptions.HTTPError:
        """
        from mydata.conf import settings
        from mydata.utils.openssh import find_or_create_key_pair

        if not self.ssh_key_pair:
            self.ssh_key_pair = find_or_create_key_pair()
        mytardis_url = settings.general.mytardis_url
        url = mytardis_url + "/api/v1/mydata_uploaderregistrationrequest/"
        urr_dict = {
            "uploader": self.resource_uri,
            "name": settings.general.instrument_name,
            "requester_name": settings.general.contact_name,
            "requester_email": settings.general.contact_email,
            "requester_public_key": self.ssh_key_pair.public_key,
            "requester_key_fingerprint": self.ssh_key_pair.fingerprint,
        }
        data = json.dumps(urr_dict)
        response = requests.post(
            headers=settings.default_headers, url=url, data=data.encode()
        )
        response.raise_for_status()
        return UploaderRegistrationRequest(urr_dict=response.json())

    def request_staging_access(self):
        """
        Check if uploads via staging are approved, and if not request approval
        """
        self.upload_uploader_info()
        self.upload_to_staging_request = self.existing_upload_to_staging_request()
        if not self.upload_to_staging_request:
            try:
                self.upload_to_staging_request = (
                    self.request_upload_to_staging_approval()
                )
                logger.debug("Uploader registration request created.")
            except PrivateKeyDoesNotExist:
                logger.debug(
                    "Generating new uploader registration request, "
                    "because private key was moved or deleted."
                )
                self.upload_to_staging_request = (
                    self.request_upload_to_staging_approval()
                )
                logger.debug(
                    "Generated new uploader registration request,"
                    " because private key was moved or deleted."
                )
        if self.upload_to_staging_request.approved:
            logger.debug("Uploads to staging have been approved!")
        else:
            logger.debug("Uploads to staging haven't been approved yet.")
        return self.upload_to_staging_request


class UploaderRegistrationRequest:
    """
    Model class for MyTardis API v1's UploaderRegistrationRequestAppResource.
    See: https://github.com/mytardis/mytardis-app-mydata/blob/master/api.py

    The upload-to-staging request contains information indicating whether the
    request has been approved i.e. the MyData.pub public key has been installed
    on the SCP server, and the approved storage box (giving the remote file
    path to upload to, and the SCP username, hostname and port).
    """

    def __init__(self, urr_dict=None):
        self.urr_dict = urr_dict

    @property
    def approved(self):
        """
        Return True if uploader registration request has been approved
        """
        return self.urr_dict["approved"]

    @property
    def approved_storage_box(self):
        """
        Return approved storage box
        """
        storagebox_dict = self.urr_dict["approved_storage_box"]
        if storagebox_dict:
            return StorageBox(storagebox_dict=storagebox_dict)
        return None

    @property
    def scp_username(self):
        """
        Return 'scp_username' storage box attribute
        """
        if not self.approved_storage_box:
            raise NoApprovedStorageBox()
        for attribute in self.approved_storage_box.attributes:
            if attribute.key == "scp_username":
                return attribute.value
        raise StorageBoxAttributeNotFound(self.approved_storage_box, "scp_username")

    @property
    def scp_hostname(self):
        """
        Return 'scp_hostname' storage box attribute
        """
        if not self.approved_storage_box:
            raise NoApprovedStorageBox()
        for attribute in self.approved_storage_box.attributes:
            if attribute.key == "scp_hostname":
                return attribute.value
        raise StorageBoxAttributeNotFound(self.approved_storage_box, "scp_hostname")

    @property
    def scp_port(self):
        """
        Return 'scp_port' storage box attribute
        """
        if not self.approved_storage_box:
            raise NoApprovedStorageBox()
        for attribute in self.approved_storage_box.attributes:
            if attribute.key == "scp_port":
                return attribute.value
        return "22"

    @property
    def location(self):
        """
        Return 'location' storage box option
        """
        if not self.approved_storage_box:
            raise NoApprovedStorageBox()
        for option in self.approved_storage_box.options:
            if option.key == "location":
                return option.value
        raise StorageBoxOptionNotFound(self.approved_storage_box, "location")
