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

    last_changed_time = models.DateTimeField(auto_now=True, blank=True)
    last_comm_time = models.DateTimeField('Time of Last Communication From Device')

    def __unicode__(self):
        if self.name:
            return "{0} ({1})".format(self.name, self.serial)
        else:
            return "Unnamed Device ({0})".format(self.serial)


class Run(models.Model):
    """
    A database representation of a single DSC run.
    As device streams temperature and heat flow data to the server,
    this data is saved on database independent of the PID controller on device.
    """
    calorimeter = models.ForeignKey(Calorimeter, verbose_name='Calorimeter')
    name = models.CharField('Nickname', max_length=100, blank=True, null=True)

    # user defined numbers
    target_temp = models.FloatField('Target Temperature (Celsius)')
    ramp_rate = models.FloatField('Rate of Temp Ramp (Celsius per second)')

    # automatically edited flags and dates to determine state of the run
    creation_time = models.DateTimeField('Creation Date', auto_now_add=True)
    start_time = models.DateTimeField('Start Time', blank=True, null=True)
    is_running = models.BooleanField('Is currently running?', blank=True, default=False)
    is_finished = models.BooleanField('Has finished running?', blank=True, default=False)

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return "Run #{0}".format(self.pk)


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

    def __unicode__(self):
        return "#{0} ({1})".format(self.pk, self.measured_at)


