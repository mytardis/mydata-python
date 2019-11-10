"""
Model class for the settings displayed in the Schedule tab
of the settings dialog and saved to disk in MyData.cfg
"""
from datetime import datetime
from datetime import timedelta

from .base import BaseSettingsModel


class ScheduleSettingsModel(BaseSettingsModel):
    """
    Model class for the settings displayed in the Schedule tab
    of the settings dialog and saved to disk in MyData.cfg
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        super(ScheduleSettingsModel, self).__init__()

        # Saved in MyData.cfg:
        self.mydata_config = dict()

        self.fields = [
            'schedule_type',
            'scheduled_date',
            'scheduled_time',
            'monday_checked',
            'tuesday_checked',
            'wednesday_checked',
            'thursday_checked',
            'friday_checked',
            'saturday_checked',
            'sunday_checked',
            'timer_from_time',
            'timer_to_time',
            'timer_minutes'
        ]

        self.default = dict(
            schedule_type="Manually",
            scheduled_date=datetime.date(datetime.now()),
            scheduled_time=datetime.time(
                datetime.now().replace(microsecond=0) + timedelta(minutes=1)),
            monday_checked=False,
            tuesday_checked=False,
            wednesday_checked=False,
            thursday_checked=False,
            friday_checked=False,
            saturday_checked=False,
            sunday_checked=False,
            timer_from_time=datetime.time(
                datetime.strptime("12:00 AM", "%I:%M %p")),
            timer_to_time=datetime.time(
                datetime.strptime("11:59 PM", "%I:%M %p")),
            timer_minutes=15)

    @property
    def schedule_type(self):
        """
        Get schedule type
        """
        return self.mydata_config['schedule_type']

    @schedule_type.setter
    def schedule_type(self, schedule_type):
        """
        Set schedule type
        """
        self.mydata_config['schedule_type'] = schedule_type

    @property
    def monday_checked(self):
        """
        Return True if Monday is ticked
        """
        return self.mydata_config['monday_checked']

    @monday_checked.setter
    def monday_checked(self, checked):
        """
        Set this to True to tick the Monday checkbox in the Schedule tab.
        """
        self.mydata_config['monday_checked'] = checked

    @property
    def tuesday_checked(self):
        """
        Return True if Tuesday is ticked
        """
        return self.mydata_config['tuesday_checked']

    @tuesday_checked.setter
    def tuesday_checked(self, checked):
        """
        Set this to True to tick the Tuesday checkbox in the Schedule tab.
        """
        self.mydata_config['tuesday_checked'] = checked

    @property
    def wednesday_checked(self):
        """
        Return True if Wednesday is ticked
        """
        return self.mydata_config['wednesday_checked']

    @wednesday_checked.setter
    def wednesday_checked(self, checked):
        """
        Set this to True to tick the Wednesday checkbox in the Schedule tab.
        """
        self.mydata_config['wednesday_checked'] = checked

    @property
    def thursday_checked(self):
        """
        Return True if Thursday is ticked
        """
        return self.mydata_config['thursday_checked']

    @thursday_checked.setter
    def thursday_checked(self, checked):
        """
        Set this to True to tick the Thursday checkbox in the Schedule tab.
        """
        self.mydata_config['thursday_checked'] = checked

    @property
    def friday_checked(self):
        """
        Return True if Friday is ticked
        """
        return self.mydata_config['friday_checked']

    @friday_checked.setter
    def friday_checked(self, checked):
        """
        Set this to True to tick the Friday checkbox in the Schedule tab.
        """
        self.mydata_config['friday_checked'] = checked

    @property
    def saturday_checked(self):
        """
        Return True if Saturday is ticked
        """
        return self.mydata_config['saturday_checked']

    @saturday_checked.setter
    def saturday_checked(self, checked):
        """
        Set this to True to tick the Saturday checkbox in the Schedule tab.
        """
        self.mydata_config['saturday_checked'] = checked

    @property
    def sunday_checked(self):
        """
        Return True if Sunday is ticked
        """
        return self.mydata_config['sunday_checked']

    @sunday_checked.setter
    def sunday_checked(self, checked):
        """
        Set this to True to tick the Sunday checkbox in the Schedule tab.
        """
        self.mydata_config['sunday_checked'] = checked

    @property
    def scheduled_date(self):
        """
        Get scheduled date
        """
        return self.mydata_config['scheduled_date']

    @scheduled_date.setter
    def scheduled_date(self, scheduled_date):
        """
        Set scheduled date
        """
        self.mydata_config['scheduled_date'] = scheduled_date

    @property
    def scheduled_time(self):
        """
        Get scheduled time
        """
        return self.mydata_config['scheduled_time']

    @scheduled_time.setter
    def scheduled_time(self, scheduled_time):
        """
        Set scheduled time
        """
        self.mydata_config['scheduled_time'] = scheduled_time

    @property
    def timer_minutes(self):
        """
        Get timer interval in minutes
        """
        return self.mydata_config['timer_minutes']

    @timer_minutes.setter
    def timer_minutes(self, timer_minutes):
        """
        Set timer interval in minutes
        """
        self.mydata_config['timer_minutes'] = timer_minutes

    @property
    def timer_from_time(self):
        """
        Get time when timer begins
        """
        return self.mydata_config['timer_from_time']

    @timer_from_time.setter
    def timer_from_time(self, timer_from_time):
        """
        Set time when timer begins
        """
        self.mydata_config['timer_from_time'] = timer_from_time

    @property
    def timer_to_time(self):
        """
        Get time when timer stops
        """
        return self.mydata_config['timer_to_time']

    @timer_to_time.setter
    def timer_to_time(self, timer_to_time):
        """
        Set time when timer stops
        """
        self.mydata_config['timer_to_time'] = timer_to_time
