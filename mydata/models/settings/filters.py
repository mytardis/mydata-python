"""
Model class for the settings displayed in the Filters tab
of the settings dialog and saved to disk in MyData.cfg
"""
from .base import BaseSettingsModel

# Used to convert ignore intervals (e.g. 3 months) into seconds:
SECONDS = dict(day=24 * 60 * 60)
SECONDS['year'] = int(365.25 * SECONDS['day'])
SECONDS['month'] = SECONDS['year'] / 12
SECONDS['week'] = 7 * SECONDS['day']


class FiltersSettingsModel(BaseSettingsModel):
    """
    Model class for the settings displayed in the Filters tab
    of the settings dialog and saved to disk in MyData.cfg
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        super(FiltersSettingsModel, self).__init__()

        # Saved in MyData.cfg:
        self.mydata_config = dict()

        self.fields = [
            'user_filter',
            'dataset_filter',
            'experiment_filter',
            'ignore_old_datasets',
            'ignore_interval_number',
            'ignore_interval_unit',
            'ignore_new_datasets',
            'ignore_new_interval_number',
            'ignore_new_interval_unit',
            'ignore_new_files',
            'ignore_new_files_minutes',
            'use_includes_file',
            'includes_file',
            'use_excludes_file',
            'excludes_file'
        ]

        self.default = dict(
            user_filter="",
            dataset_filter="",
            experiment_filter="",
            ignore_old_datasets=False,
            ignore_interval_number=0,
            ignore_interval_unit="months",
            ignore_new_datasets=False,
            ignore_new_interval_number=0,
            ignore_new_interval_unit="months",
            ignore_new_files=True,
            ignore_new_files_minutes=1,
            use_includes_file=False,
            includes_file="",
            use_excludes_file=False,
            excludes_file=""
        )

    @property
    def user_filter(self):
        """
        Get glob for matching user folders
        """
        return self.mydata_config['user_filter']

    @user_filter.setter
    def user_filter(self, user_filter):
        """
        Set glob for matching user folders
        """
        self.mydata_config['user_filter'] = user_filter

    @property
    def dataset_filter(self):
        """
        Get glob for matching dataset folders
        """
        return self.mydata_config['dataset_filter']

    @dataset_filter.setter
    def dataset_filter(self, dataset_filter):
        """
        Set glob for matching dataset folders
        """
        self.mydata_config['dataset_filter'] = dataset_filter

    @property
    def experiment_filter(self):
        """
        Get glob for matching experiment folders
        """
        return self.mydata_config['experiment_filter']

    @experiment_filter.setter
    def experiment_filter(self, experiment_filter):
        """
        Set glob for matching experiment folders
        """
        self.mydata_config['experiment_filter'] = experiment_filter

    @property
    def ignore_old_datasets(self):
        """
        Returns True if MyData should ignore old dataset folders
        """
        return self.mydata_config['ignore_old_datasets']

    @ignore_old_datasets.setter
    def ignore_old_datasets(self, ignore_old_datasets):
        """
        Set this to True if MyData should ignore old dataset folders
        """
        self.mydata_config['ignore_old_datasets'] = ignore_old_datasets

    @property
    def ignore_old_datasets_interval_number(self):
        """
        Return the number of days/weeks/months used to define an old dataset
        """
        return self.mydata_config['ignore_interval_number']

    @ignore_old_datasets_interval_number.setter
    def ignore_old_datasets_interval_number(self, ignore_old_datasets_interval_number):
        """
        Set the number of days/weeks/months used to define an old dataset
        """
        self.mydata_config['ignore_interval_number'] = \
            ignore_old_datasets_interval_number

    @property
    def ignore_old_datasets_interval_unit(self):
        """
        Return the time interval unit (days/weeks/months)
        used to define an old dataset
        """
        return self.mydata_config['ignore_interval_unit']

    @ignore_old_datasets_interval_unit.setter
    def ignore_old_datasets_interval_unit(self, ignore_old_datasets_interval_unit):
        """
        Set the time interval unit (days/weeks/months)
        used to define an old dataset
        """
        self.mydata_config['ignore_interval_unit'] = \
            ignore_old_datasets_interval_unit

    @property
    def ignore_old_datasets_interval_seconds(self):
        """
        Return the interval (in seconds) beyond which
        old datasets will be ignored.
        """
        singular_ignore_interval_unit = \
            self.mydata_config['ignore_interval_unit'].rstrip('s')
        return self.mydata_config['ignore_interval_number'] * \
            SECONDS[singular_ignore_interval_unit]

    @property
    def ignore_new_datasets(self):
        """
        Returns True if MyData should ignore new dataset folders
        """
        return self.mydata_config['ignore_new_datasets']

    @ignore_new_datasets.setter
    def ignore_new_datasets(self, ignore_new_datasets):
        """
        Set this to True if MyData should ignore new dataset folders
        """
        self.mydata_config['ignore_new_datasets'] = ignore_new_datasets

    @property
    def ignore_new_datasets_interval_number(self):
        """
        Return the number of days/weeks/months used to define an new dataset
        """
        return self.mydata_config['ignore_new_interval_number']

    @ignore_new_datasets_interval_number.setter
    def ignore_new_datasets_interval_number(self, ignore_new_datasets_interval_number):
        """
        Set the number of days/weeks/months used to define an new dataset
        """
        self.mydata_config['ignore_new_interval_number'] = \
            ignore_new_datasets_interval_number

    @property
    def ignore_new_datasets_interval_unit(self):
        """
        Return the time interval unit (days/weeks/months)
        used to define an new dataset
        """
        return self.mydata_config['ignore_new_interval_unit']

    @ignore_new_datasets_interval_unit.setter
    def ignore_new_datasets_interval_unit(self, ignore_new_datasets_interval_unit):
        """
        Set the time interval unit (days/weeks/months)
        used to define an new dataset
        """
        self.mydata_config['ignore_new_interval_unit'] = \
            ignore_new_datasets_interval_unit

    @property
    def ignore_new_datasets_interval_seconds(self):
        """
        Return the interval (in seconds) beyond which
        old datasets will be ignored.
        """
        singular_ignore_interval_unit = \
            self.mydata_config['ignore_new_interval_unit'].rstrip('s')
        return self.mydata_config['ignore_new_interval_number'] * \
            SECONDS[singular_ignore_interval_unit]

    @property
    def ignore_new_files(self):
        """
        Returns True if MyData should ignore recently modified files
        """
        return self.mydata_config['ignore_new_files']

    @ignore_new_files.setter
    def ignore_new_files(self, ignore_new_files):
        """
        Set this to True if MyData should ignore recently modified files
        """
        self.mydata_config['ignore_new_files'] = ignore_new_files

    @property
    def ignore_new_files_minutes(self):
        """
        Return the number of minutes used to define a recently modified file
        """
        return self.mydata_config['ignore_new_files_minutes']

    @ignore_new_files_minutes.setter
    def ignore_new_files_minutes(self, ignore_new_files_minutes):
        """
        Set the number of minutes used to define a recently modified file
        """
        self.mydata_config['ignore_new_files_minutes'] = ignore_new_files_minutes

    @property
    def use_includes_file(self):
        """
        Return True if using an includes file to only upload files matching
        glob patterns listed in the includes file.
        """
        return self.mydata_config['use_includes_file']

    @use_includes_file.setter
    def use_includes_file(self, use_includes_file):
        """
        Set to True if using an includes file to only upload files matching
        glob patterns listed in the includes file.
        """
        self.mydata_config['use_includes_file'] = use_includes_file

    @property
    def includes_file(self):
        """
        Return path to an includes file, used to only upload files matching
        glob patterns listed in the includes file.
        """
        return self.mydata_config['includes_file']

    @includes_file.setter
    def includes_file(self, includes_file):
        """
        Set path to an includes file, used to only upload files matching
        glob patterns listed in the includes file.
        """
        self.mydata_config['includes_file'] = includes_file

    @property
    def use_excludes_file(self):
        """
        Return True if using an excludes file to prevent uploads of files
        matching glob patterns listed in the excludes file.
        """
        return self.mydata_config['use_excludes_file']

    @use_excludes_file.setter
    def use_excludes_file(self, use_excludes_file):
        """
        Set to True if using an excludes file to prevent uploads of files
        matching glob patterns listed in the excludes file.
        """
        self.mydata_config['use_excludes_file'] = use_excludes_file

    @property
    def excludes_file(self):
        """
        Return path to an excludes file, used to only upload files matching
        glob patterns listed in the excludes file.
        """
        return self.mydata_config['excludes_file']

    @excludes_file.setter
    def excludes_file(self, excludes_file):
        """
        Set path to an excludes file, used to only upload files matching
        glob patterns listed in the excludes file.
        """
        self.mydata_config['excludes_file'] = excludes_file
