"""
Model class for representing a local file
"""
import os


class LocalFile:
    """
    Model class for representing a local file
    """

    def __init__(self, filepath, directory, uploaded):

        # The file path, e.g. '/path/to/image.jpg':
        self.filepath = filepath

        # The relative directory within the dataset folder, e.g. '':
        self.directory = directory

        # Whether the file has been uploaded:
        self.uploaded = uploaded

    @property
    def filename(self):
        """Return the filename, e.g. 'image.jpg'
        """
        return os.path.basename(self.filepath)
