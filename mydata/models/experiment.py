"""
Model class for MyTardis API v1's ExperimentResource.
"""
# pylint: disable=broad-except
import json

from urllib.parse import quote

import requests

from ..conf import settings
from ..threads.flags import FLAGS
from ..logs import logger
from .objectacl import ObjectACL


class Experiment:
    """
    Model class for MyTardis API v1's ExperimentResource.
    """

    def __init__(self, exp_dict):
        self.id = None  # pylint: disable=invalid-name
        self.title = None
        self.resource_uri = None
        self.__dict__.update(exp_dict)

    @staticmethod
    def get_or_create_exp_for_folder(folder):
        """
        See also get_exp_for_folder, create_exp_for_folder
        """
        existing_exp = Experiment.get_exp_for_folder(folder)
        if not existing_exp:
            return Experiment.create_exp_for_folder(folder)
        if FLAGS.test_run_running:
            message = (
                "ADDING TO EXISTING EXPERIMENT FOR FOLDER: %s\n"
                "    URL: %s/%s\n"
                "    Title: %s\n"
                "    Owner: %s"
                % (
                    folder.get_rel_path(),
                    settings.general.mytardis_url,
                    existing_exp.view_uri,
                    existing_exp.title,
                    folder.owner.username,
                )
            )
            logger.testrun(message)
        return existing_exp

    @staticmethod
    def get_exp_for_folder(folder):
        """
        See also get_or_create_exp_for_folder
        """
        exp_title_encoded = quote(folder.experiment_title.encode("utf-8"))
        folder_structure_encoded = quote(settings.advanced.folder_structure)
        url = (
            "%s/api/v1/mydata_experiment/?format=json"
            "&title=%s&folder_structure=%s"
            % (
                settings.general.mytardis_url,
                exp_title_encoded,
                folder_structure_encoded,
            )
        )
        if folder.user_folder_name:
            url += "&user_folder_name=%s" % quote(
                folder.user_folder_name.encode("utf-8")
            )
        if folder.group_folder_name:
            url += "&group_folder_name=%s" % quote(
                folder.group_folder_name.encode("utf-8")
            )

        logger.debug(url)
        response = requests.get(url=url, headers=settings.default_headers)
        response.raise_for_status()
        experiments_dict = response.json()
        num_exps_found = experiments_dict["meta"]["total_count"]
        if num_exps_found == 0:
            Experiment.log_exp_not_found(folder)
            return None
        if num_exps_found >= 1:
            Experiment.log_exp_found(folder)
            return Experiment(experiments_dict["objects"][0])

        # Should never reach this, but it keeps Pylint happy:
        return None

    @staticmethod
    def create_exp_for_folder(folder):
        """
        Create a MyTardis experiment to create this folder's dataset within
        """
        user_folder_name = folder.user_folder_name
        group_folder_name = folder.group_folder_name
        try:
            owner_user_id = folder.owner.id
        except Exception:
            owner_user_id = None

        instrument_name = settings.general.instrument.name
        exp_title = folder.experiment_title

        Experiment.log_exp_creation(folder)
        if user_folder_name:
            description = (
                "Instrument: %s\n"
                "User folder name: %s\n"
                "Uploaded from: %s:%s"
                % (
                    instrument_name,
                    user_folder_name,
                    settings.uploader.hostname,
                    folder.location,
                )
            )
            if group_folder_name:
                description += "\nGroup folder name: %s" % group_folder_name
        else:
            description = (
                "Instrument: %s\n"
                "Group folder name: %s\n"
                "Uploaded from: %s:%s"
                % (
                    instrument_name,
                    group_folder_name,
                    settings.uploader.hostname,
                    folder.location,
                )
            )

        if FLAGS.test_run_running:
            message = (
                "CREATING NEW EXPERIMENT FOR FOLDER: %s\n"
                "    Title: %s\n"
                "    Description: \n"
                "        Instrument: %s\n"
                "        User folder name: %s\n"
                "    Owner: %s"
                % (
                    folder.get_rel_path(),
                    exp_title,
                    instrument_name,
                    user_folder_name,
                    folder.owner.username,
                )
            )
            logger.testrun(message)
            return None

        exp_dict = {
            "title": exp_title,
            "description": description,
            "immutable": False,
            "parameter_sets": [
                {
                    "schema": "http://mytardis.org/schemas" "/mydata/defaultexperiment",
                    "parameters": [
                        {"name": "uploader", "value": settings.miscellaneous.uuid},
                        {"name": "user_folder_name", "value": user_folder_name},
                    ],
                }
            ],
        }
        if group_folder_name:
            exp_dict["parameter_sets"][0]["parameters"].append(
                {"name": "group_folder_name", "value": group_folder_name}
            )
        url = "%s/api/v1/mydata_experiment/" % settings.general.mytardis_url
        logger.debug(url)
        response = requests.post(
            headers=settings.default_headers,
            url=url,
            data=json.dumps(exp_dict).encode(),
        )
        response.raise_for_status()
        created_exp_dict = response.json()
        created_exp = Experiment(created_exp_dict)
        message = (
            "Succeeded in creating experiment '%s' for uploader "
            '"%s" and user folder "%s"' % (exp_title, instrument_name, user_folder_name)
        )
        if group_folder_name:
            message += ' and group folder "%s"' % group_folder_name
        logger.debug(message)

        facility_managers_group = settings.general.facility.manager_group
        ObjectACL.share_exp_with_group(
            created_exp, facility_managers_group, is_owner=True
        )
        # Avoid creating a duplicate ObjectACL if the user folder's
        # username matches the facility manager's username.
        # Don't attempt to create an ObjectACL record for an
        # invalid user (without a MyTardis user ID).
        if (
            settings.general.username != folder.owner.username
            and owner_user_id is not None
        ):
            ObjectACL.share_exp_with_user(created_exp, folder.owner)
        if folder.group is not None and folder.group.id != facility_managers_group.id:
            ObjectACL.share_exp_with_group(created_exp, folder.group, is_owner=True)
        return created_exp

    @property
    def exp_id(self):
        """
        Return the experiment ID
        """
        return self.__dict__["id"]

    @property
    def view_uri(self):
        """
        Return the experiment's view URI
        """
        return "experiment/view/%d/" % self.exp_id

    @staticmethod
    def log_exp_creation(folder):
        """
        Log a message about the experiment's creation
        """
        instrument_name = settings.general.instrument.name

        if folder.user_folder_name:
            message = (
                "Creating experiment for instrument '%s', "
                "user folder '%s'." % (instrument_name, folder.user_folder_name)
            )
            if folder.group_folder_name:
                message += ", group folder : '%s'" % folder.group_folder_name
        elif folder.group_folder_name:
            message = (
                "Creating experiment for uploader '%s', "
                "user group folder '%s'." % (instrument_name, folder.group_folder_name)
            )
        else:
            message = "Creating experiment for uploader '%s'" % instrument_name
        logger.info(message)
        return message

    @staticmethod
    def log_exp_not_found(folder):
        """
        Log a message about an experiment not being found.  This doesn't
        deserve a warning-level log message, because it's quite normal for
        MyData to find that it needs to create an experiment rather than
        using an existing one.
        """
        if folder.user_folder_name:
            message = "Experiment not found for %s, '%s'" % (
                folder.user_folder_name,
                folder.experiment_title,
            )
            if folder.group_folder_name:
                message += ", '%s'" % folder.group_folder_name
        elif folder.group_folder_name:
            message = "Experiment not found for %s, '%s'" % (
                folder.group_folder_name,
                folder.experiment_title,
            )
        else:
            message = "Experiment not found for '%s'" % folder.experiment_title
        logger.debug(message)
        return message

    @staticmethod
    def log_exp_found(folder):
        """
        Log a message about an existing experiment being found
        """
        if folder.user_folder_name:
            message = (
                "Found existing experiment with title '%s' "
                "and user folder '%s'"
                % (folder.experiment_title, folder.user_folder_name)
            )
            if folder.group_folder_name:
                message += " and group folder '%s'." % folder.group_folder_name
        elif folder.group_folder_name:
            message = (
                "Found existing experiment with title '%s' "
                "and user group folder '%s'"
                % (folder.experiment_title, folder.group_folder_name)
            )
        else:
            message = (
                "Found existing experiment with title '%s'." % folder.experiment_title
            )
        logger.debug(message)
        return message
