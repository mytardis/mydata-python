"""
Model class for the settings displayed in the Advanced tab
of the settings dialog and saved to disk in MyData.cfg
"""


class AdvancedSettings:
    """
    Model class for the settings displayed in the Advanced tab
    of the settings dialog and saved to disk in MyData.cfg
    """

    def __init__(self):
        # Saved in MyData.cfg:
        self.mydata_config = dict()

        self.fields = [
            "folder_structure",
            "group_prefix",
            "validate_folder_structure",
            "max_lookup_threads",
            "max_upload_retries",
            "upload_invalid_user_or_group_folders",
            "upload_method"
        ]

    @property
    def folder_structure(self):
        """
        Get folder structure
        """
        return self.mydata_config["folder_structure"]

    @folder_structure.setter
    def folder_structure(self, folder_structure):
        """
        Set folder structure
        """
        self.mydata_config["folder_structure"] = folder_structure

    @property
    def validate_folder_structure(self):
        """
        Returns True if folder structure should be validated
        """
        return self.mydata_config["validate_folder_structure"]

    @validate_folder_structure.setter
    def validate_folder_structure(self, validate_folder_structure):
        """
        Set this to True if folder structure should be validated
        """
        self.mydata_config["validate_folder_structure"] = validate_folder_structure

    @property
    def upload_invalid_user_or_group_folders(self):
        """
        Returns True if data folders should be scanned and uploaded even if
        MyData can't find a MyTardis user (or group) record corresponding to
        the the user (or group) folder.
        """
        return self.mydata_config["upload_invalid_user_or_group_folders"]

    @upload_invalid_user_or_group_folders.setter
    def upload_invalid_user_or_group_folders(
        self, upload_invalid_user_or_group_folders
    ):
        """
        Set this to True if data folders should be scanned and uploaded even if
        MyData can't find a MyTardis user (or group) record corresponding to
        the the user (or group) folder.
        """
        self.mydata_config[
            "upload_invalid_user_or_group_folders"
        ] = upload_invalid_user_or_group_folders

    @property
    def group_prefix(self):
        """
        Return prefix prepended to group folder name to match MyTardis group
        """
        return self.mydata_config["group_prefix"]

    @property
    def max_lookup_threads(self):
        """
        Get the maximum number of lookup threads
        """
        return int(self.mydata_config["max_lookup_threads"])

    @property
    def max_upload_retries(self):
        """
        Get the maximum number of retries per upload
        """
        return int(self.mydata_config["max_upload_retries"])

    def set_defaults(self):
        """
        Set default values for configuration parameters
        that will appear in MyData.cfg for fields in the
        Settings Dialog's Filter tab
        """
        self.mydata_config["folder_structure"] = "Username / Dataset"
        self.mydata_config["group_prefix"] = ""
        self.mydata_config["validate_folder_structure"] = True
        self.mydata_config["max_lookup_threads"] = 1
        self.mydata_config["max_upload_retries"] = 1
        self.mydata_config["upload_invalid_user_or_group_folders"] = True

    @property
    def upload_method(self):
        """
        Return upload method
        """
        return self.mydata_config["upload_method"]
