"""
Model class for MyTardis API v1's ObjectACLResource.
"""

import json
import requests

from ..conf import settings
from ..logs import logger


class ObjectACL:
    """
    Model class for MyTardis API v1's ObjectACLResource.
    """

    @staticmethod
    def share_exp_with_user(experiment, user):
        """
        Grants full ownership of experiment to user.
        """
        logger.debug(
            '\nSharing via ObjectACL with username "' + user.username + '"...\n'
        )

        mytardis_url = settings.general.mytardis_url

        object_acl_dict = {
            "pluginId": "django_user",
            "entityId": str(user.id),
            "content_object": experiment.resource_uri.replace("mydata_", ""),
            "content_type": "experiment",
            "object_id": experiment.exp_id,
            "aclOwnershipType": 1,
            "isOwner": True,
            "canRead": True,
            "canWrite": True,
            "canDelete": False,
            "effectiveDate": None,
            "expiryDate": None,
        }

        url = mytardis_url + "/api/v1/objectacl/"
        response = requests.post(
            headers=settings.default_headers,
            url=url,
            data=json.dumps(object_acl_dict).encode(),
        )
        response.raise_for_status()
        logger.debug("Shared experiment with user " + user.username + ".")

    @staticmethod
    def share_exp_with_group(experiment, group, is_owner):
        """
        Grants read access to experiment to group.
        """
        logger.debug('\nSharing via ObjectACL with group "' + group.name + '"...\n')

        mytardis_url = settings.general.mytardis_url

        object_acl_dict = {
            "pluginId": "django_group",
            "entityId": str(group.id),
            "content_object": experiment.resource_uri.replace("mydata_", ""),
            "content_type": "experiment",
            "object_id": experiment.exp_id,
            "aclOwnershipType": 1,
            "isOwner": is_owner,
            "canRead": True,
            "canWrite": True,
            "canDelete": False,
            "effectiveDate": None,
            "expiryDate": None,
        }

        url = mytardis_url + "/api/v1/objectacl/"
        response = requests.post(
            headers=settings.default_headers,
            url=url,
            data=json.dumps(object_acl_dict).encode(),
        )
        response.raise_for_status()
        logger.debug("Shared experiment with group " + group.name + ".")
