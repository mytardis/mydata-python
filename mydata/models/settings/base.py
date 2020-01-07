"""
Base class for deriving a model class for the settings
displayed in each tab of the settings dialog
"""


class BaseSettings:
    """
    Base class for deriving a model class for the settings
    displayed in each tab of the settings dialog
    """

    def __init__(self):
        # Saved in MyData.cfg:
        self.mydata_config = dict()

        self.fields = []

        self.default = dict()

    def set_default_for_field(self, field):
        """
        Set default value for one field.
        """
        self.mydata_config[field] = self.default[field]

    def set_defaults(self):
        """
        Set default values for configuration parameters
        that will appear in MyData.cfg for fields in the
        Settings Dialog's Filter tab
        """
        for field in self.fields:
            self.set_default_for_field(field)
