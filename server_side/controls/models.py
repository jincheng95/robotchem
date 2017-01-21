""" Models for the website database.

Jin Cheng, 2/12/16

"""
from django.db import models


class Calorimeter(models.Model):
    """
    A database representation of a calorimeter.
    Saves connection times on server to determine whether device is offline,
    and whether user at browser can access / control the device.
    """
    serial = models.CharField('Raspberry Pi Serial', max_length=50, unique=True)
    access_code = models.CharField('Access Code', max_length=100)
    name = models.CharField('Nickname', max_length=100, blank=True, null=True)
    creation_time = models.DateTimeField(auto_now_add=True, blank=True)

    current_sample_temp = models.FloatField(null=True, blank=True)
    current_ref_temp = models.FloatField(null=True, blank=True)

    K_p = models.FloatField("PID Proportionality Factor", default=5., blank=True)
    K_i = models.FloatField("PID Integral Factor", default=1., blank=True)
    K_d = models.FloatField("PID Derivative Factor", default=0.0003, blank=True)
    temp_tolerance_range = models.FloatField("Temperature tolerance", default=1., blank=True)
    temp_tolerance_duration = models.FloatField("Stabilization duration", default=15., blank=True)
    max_ramp_rate = models.FloatField("Max Ramp Rate", default=5., blank=True)
    idle_loop_interval = models.FloatField("Web API Refresh Rate when no jobs are running", default=10., blank=True)
    active_loop_interval = models.FloatField("Web API / PID Calculation Refresh Rate with job running", default=5.)
    web_api_min_upload_length = models.IntegerField("Minimum number of data points to collect before uploading",
                                                    default=5)

    last_changed_time = models.DateTimeField(auto_now=True, blank=True)
    last_comm_time = models.DateTimeField('Time of Last Communication From Device')

    stop_flag = models.BooleanField('Stop Flag', default=False, blank=True)

    def __repr__(self):
        if self.name:
            return "{0} ({1})".format(self.name, self.serial)
        else:
            return "Unnamed Device ({0})".format(self.serial)

    def __str__(self):
        return self.__repr__()

    class Meta:
        app_label = "controls"


class Run(models.Model):
    """
    A database representation of a single DSC run.
    As device streams temperature and heat flow data to the server,
    this data is saved on database independent of the PID controller on device.
    """
    calorimeter = models.ForeignKey(Calorimeter, verbose_name='Calorimeter')
    name = models.CharField('Nickname', max_length=100, blank=True, null=True)

    # user defined numbers
    start_temp = models.FloatField('Start Temperature (Celsius)')
    target_temp = models.FloatField('Target Temperature (Celsius)')
    ramp_rate = models.FloatField('Rate of Temp Ramp (Celsius per minute)')

    # automatically edited flags and dates to determine state of the run
    creation_time = models.DateTimeField('Creation Date', auto_now_add=True)
    start_time = models.DateTimeField('Start Time', blank=True, null=True)
    finish_time = models.DateTimeField('Finish Time', blank=True, null=True)

    stabilized_at_start = models.BooleanField('Temp Has Stabilized at Start Temp', blank=True, default=False)
    is_ready = models.BooleanField('Is Ready to Start?', blank=True, default=False)
    is_running = models.BooleanField('Is currently running?', blank=True, default=False)
    is_finished = models.BooleanField('Has finished running?', blank=True, default=False)

    email = models.EmailField('Notification Email Address', blank=True, null=True)

    def __repr__(self):
        if self.name:
            return self.name
        else:
            return "Run #{0}".format(self.pk)

    def __str__(self):
        return self.__repr__()

    class Meta:
        app_label = "controls"


class DataPoint(models.Model):
    """
    A database representation of data measurements associated with a single point in time.
    When a measurement is made on device, it is streamed to the server to be saved here.
    """
    run = models.ForeignKey(Run, verbose_name="Run")

    # time of measurement is saved independently to eliminate inconsistent network lags
    measured_at = models.DateTimeField("Measured At")
    received_at = models.DateTimeField("Received At", auto_now_add=True, blank=True)

    # measurements made on device
    temp_ref = models.FloatField("Reference Temp (Celsius)")
    temp_sample = models.FloatField("Sample Temp (Celsius)")
    heat_ref = models.FloatField("Reference Heat Flow Since Last (Joules)")
    heat_sample = models.FloatField("Sample Heat Flow Since Last (Joules)")

    def __repr__(self):
        return "#{0} ({1})".format(self.pk, self.measured_at)

    def __str__(self):
        return self.__repr__()

    class Meta:
        app_label = "controls"


