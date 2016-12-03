"""
This module contains GPIO hardware controls for
1. the temperature sensors,
2. the electric heaters (PID controlled),
3. the LEDs.

Functions inside this script are meant to be called by multithreaded processes
rather than the main process.
"""

import RPi.GPIO as GPIO
import gpiozero
from w1thermsensor import W1ThermSensor
import time
from .settings import PINS, PID_PARAMS, TEMP_SENSOR_ID_REF, TEMP_SENSOR_ID_SAMPLE


class PID(object):
    """
    An object representing a PID controller,
    allowing the two heaters to have separate PID params.

    Stores historical integral and derivative values so far,
    while the set point can be updated after class construction and at any point in time.
    """

    def __init__(self, init_val, Kp=None, Ki=None, Kd=None):
        """
        Class constructor.

        :param init_val: initial value,
        :param Kp: custom PID proportionality factor,
        :param Ki: custom PID integral factor,
        :param Kd: custom PID derivative factor.
        """
        self.init_val = float(init_val)
        self.set_point = None
        self.last_error, self.proportional, self.integral, self.derivative = 0., 0., 0., 0.

        # if not specified in object construction, use the PID params in settings.py
        self.Kp = Kp or PID_PARAMS['P']
        self.Ki = Ki or PID_PARAMS['I']
        self.Kd = Kd or PID_PARAMS['D']

        self.last_time = time.time()

    def set_setpoint(self, set_point):
        self.set_point = float(set_point)

    def clear(self):
        """
        Clears PID computations and coefficients.
        """
        self.set_point = 0.
        self.proportional, self.integral, self.derivative, self.last_error = 0., 0., 0., 0.

    def update(self, feedback_value):
        """
        Calculates PID output for a given feedback from sensor.

        :param feedback_value: temperature reading
        :return: PID output for current time:
        u(t) = K_p e(t) + K_i \int_{0}^{t} e(t) dt + K_d {de}/{dt}
        """
        error = self.set_point - feedback_value
        delta_error = error - self.last_error

        now = time.time()
        delta_time = now - self.last_time

        self.proportional = self.Kp * error
        self.integral += delta_time * error
        self.derivative = delta_error / delta_time

        # reset last_time and last_error for next calculation
        self.last_error, self.last_time = error, now

        return self.proportional + self.Ki*self.integral + self.Kd*self.derivative

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __unicode__(self):
        return "<PID controller object (Kp, Ki, Kd)=({0}, {1}, {2}) " \
               "SP={3} IV={4}>".format(self.Kp, self.Ki, self.Kd, self.set_point, self.init_val)


def _initialise_sensor(sensor_id, model=W1ThermSensor.THERM_SENSOR_DS18B20):
    available_sensor_ids = [sensor.id for sensor in W1ThermSensor.get_available_sensors()]
    if sensor_id not in available_sensor_ids:
        raise AssertionError("Cannot find sensor with this sensor id.")
    return W1ThermSensor(model, sensor_id)


def read_from_sample():
    try:
        global SAMPLE_SENSOR
    except NameError:
        SAMPLE_SENSOR = _initialise_sensor(TEMP_SENSOR_ID_SAMPLE)
        globals()['SAMPLE_SENSOR'] = SAMPLE_SENSOR
    return SAMPLE_SENSOR.get_temperature()


def read_from_ref():
    try:
        global REF_SENSOR
    except NameError:
        REF_SENSOR = _initialise_sensor(TEMP_SENSOR_ID_REF)
        globals()['REF_SENSOR'] = REF_SENSOR
    return REF_SENSOR.get_temperature()


def read_from_average():
    return (read_from_sample() + read_from_ref()) / 2
