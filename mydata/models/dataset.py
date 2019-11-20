"""
Model class for MyTardis API v1's DatasetResource.
"""
import json
import requests
from six.moves import urllib

from ..conf import settings
from ..threads.flags import FLAGS
from ..logs import logger


class Dataset():
    """
    Client-side model for caching results of querying
    MyTardis's dataset model.
    """
    def __init__(self, dataset_dict):
        self.id = None  # pylint: disable=invalid-name
        self.description = None
        self.immutable = None
        self.resource_uri = None
        self.__dict__.update(dataset_dict)

    @property
    def dataset_id(self):
        """
        Return the dataset ID
        """
        return self.__dict__['id']

    @property
    def view_uri(self):
        """
        Return the dataset's view URI, as used in the MyData class's
        OnMyTardis method.
        """
        return "dataset/%s" % self.__dict__['id']

    @staticmethod
    def create_dataset_if_necessary(folder):
        """
        Create a dataset if we don't already have one for this folder.

        First we check if a suitable dataset already exists.
        """
        experiment = folder.experiment
        existing_dataset = Dataset.get_dataset(folder)
        if existing_dataset:
            if FLAGS.test_run_running:
                message = "ADDING TO EXISTING DATASET FOR FOLDER: %s\n" \
                    "    URL: %s/%s\n" \
                    "    Description: %s\n" \
                    "    In Experiment: %s/%s" \
                    % (folder.get_rel_path(), settings.general.mytardis_url,
                       existing_dataset.view_uri, existing_dataset.description,
                       settings.general.mytardis_url,
                       experiment.view_uri if experiment else "experiment/?")
                logger.testrun(message)
            return existing_dataset

        # We need to create a new dataset:
        description = folder.name
        logger.debug("Creating dataset record for folder: " + description)
        if FLAGS.test_run_running:
            message = "CREATING NEW DATASET FOR FOLDER: %s\n" \
                "    Description: %s" \
                % (folder.get_rel_path(), description)
            if experiment:  # Could be None in test run.
                message += "\n    In Experiment: %s/%s" \
                    % (settings.general.mytardis_url, experiment.view_uri)
            logger.testrun(message)
            return None
        mytardis_url = settings.general.mytardis_url
        exp_uri = experiment.resource_uri.replace(
            'mydata_experiment', 'experiment') if experiment else None
        dataset_dict = {
            "instrument": settings.general.instrument.resource_uri,
            "description": description,
            "experiments": [exp_uri],
            "immutable": False}
        data = json.dumps(dataset_dict)
        url = "%s/api/v1/dataset/" % mytardis_url
        response = requests.post(headers=settings.default_headers,
                                 url=url, data=data.encode())
        response.raise_for_status()
        new_dataset_dict = response.json()
        return Dataset(new_dataset_dict)

    @staticmethod
    def get_dataset(folder):
        """
        Get the dataset record for this folder

        If multiple datasets are found matching the folder, we return the first
        one and log a warning.  We could raise a MultipleObjectsReturned
        exception, but generally it is better to ensure that the data is
        uploaded, rather than have MyData refuse to upload because a duplicate
        dataset has been created on the server.

        If no matching dataset is found, we return None
        """
        if not folder.experiment:
            # folder.experiment could be None in testRun
            return None
        description = urllib.parse.quote(folder.name.encode('utf-8'))
        url = ("%s/api/v1/dataset/?format=json&experiments__id=%s"
               "&description=%s" % (settings.general.mytardis_url,
                                    folder.experiment.exp_id,
                                    description))
        url_with_instrument = "%s&instrument__id=%s"\
            % (url, settings.general.instrument.instrument_id)
        response = requests.get(
            headers=settings.default_headers, url=url_with_instrument)
        if response.status_code == 400:
            logger.debug(
                "MyTardis doesn't support filtering datasets by instrument")
            response = requests.get(headers=settings.default_headers, url=url)
        response.raise_for_status()
        datasets_dict = response.json()
        num_datasets = datasets_dict['meta']['total_count']
        if num_datasets == 0:
            return None
        if num_datasets > 1:
            logger.warning(
                "WARNING: Found multiple datasets for folder %s" % description)
        if num_datasets == 1:
            logger.debug("Found existing dataset for folder %s" % description)
        return Dataset(datasets_dict['objects'][0])
