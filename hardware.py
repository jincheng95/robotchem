"""
This module contains GPIO hardware controls for
1. the temperature sensors,
2. the electric heaters (PID controlled),
3. the LEDs.

Jin Cheng & Hayley Weir 08/12/16:
    the PID class

Hayley Weir 11/12/16:
    GPIO controls,
    LED controls,
    initialisation function,
    hardware components testing

Jin Cheng 12/12/16:
    function cleanup and asynchronisation, introduced wrappers
    the asynchronous PWM control queue
    documentation
"""

import asyncio
import os
import subprocess
import time

import settings
from utils import clamp

if not settings.SIMULATE_HARDWARE:
    import Adafruit_ADS1x15
    import RPi.GPIO as GPIO
else:
    import random


class PID(object):
    """
    An object representing a PID controller,
    allowing the two heaters to have separate PID params.

    Stores historical integral and derivative values so far,
    while the set point can be updated after class construction and at any point in time.
    """

    def __init__(self, init_val, Kp=None, Ki=None, Kd=None, set_point=None):
        """
        Class constructor.

        :param init_val: initial value,
        :param Kp: custom PID proportionality factor,
        :param Ki: custom PID integral factor,
        :param Kd: custom PID derivative factor.
        """
        self.init_val = float(init_val)
        self.set_point = set_point
        self.last_error, self.proportional, self.integral, self.derivative = 0., 0., 0., 0.

        # if not specified in object construction, use the PID params in settings.py
        self.Kp = Kp or settings.PID_PARAMS['P']
        self.Ki = Ki or settings.PID_PARAMS['I']
        self.Kd = Kd or settings.PID_PARAMS['D']

        self.last_time = time.time()

    def set_setpoint(self, set_point):
        self.set_point = float(set_point)

    def clear(self):
        """Clears PID computations and coefficients.
        """
        self.set_point = 0.
        self.proportional, self.integral, self.derivative, self.last_error = 0., 0., 0., 0.

    def update(self, feedback_value):
        """Calculates PID output for a given feedback from sensor.

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


async def _change_heater_pwm(pid_object, queue, temperature, pwm_object):
    """An asynchronous queue consumer to change PWM output.
    if a setpoint is in the queue, the PWM will be changed on the specified pin number."""
    while True:
        set_point = await queue.get()
        pid_object.set_setpoint(set_point)
        duty_cycle = clamp(pid_object.update(temperature))
        pwm_object.ChangeDutyCycle(duty_cycle)



HAS_INITIALZED_MODPROBE = False
debug_temp = 0

async def _read_temp(identifier):
    """
    Reads from the One-Wire thermocouple temperature info from its bus.
    :param identifier: the unique device identifier
    :return: temperature, in Celsius
    """

    # if debug, return some random value for testing
    if settings.SIMULATE_HARDWARE:
        global debug_temp
        debug_temp += 0.2
        await asyncio.sleep(random.random() * 0.1) # simulate slow I/O
        return random.gauss(debug_temp, 0.5)

    global HAS_INITIALZED_MODPROBE
    if not HAS_INITIALZED_MODPROBE:
        # Initialize the GPIO Pins, then change the global flag
        subprocess.call(['sudo', 'modprobe', 'w1-gpio'])
        subprocess.call(['sudo', 'modprobe', 'w1-therm'])
        HAS_INITIALZED_MODPROBE = True

    # Absolute file path of the OneWire serial comm
    device_file = os.path.join(settings.TEMP_SENSOR_BASE_DIR, identifier, settings.TEMP_SENSOR_ID_APPENDIX)

    # Reads temperature data
    def read_temp_from_file(device_file):
        with open(device_file, 'r') as f:
            lines = f.readlines()
        return lines

    # While the first line does not contain 'YES', wait for 0.2s and then read the device file again
    lines = read_temp_from_file(device_file)
    while lines[0].strip()[-3:] != "YES":
        time.sleep(settings.TEMP_READ_TIME_INTERVAL)
        lines = read_temp_from_file(device_file)

    # Look for the position of the '=' in the second line of the device file.
    equals_pos = lines[1].find('t=')

    # If the '=' is found, convert the rest of the line after the '=' into degrees Celsius,
    if equals_pos != -1:
        temp_string = lines[1][equals_pos + 2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

    # If temperature read is not found,
    # return a very large number to suspend heating until a proper measurement is made
    return 99999


async def read_temp_ref():
    """
    Reads reference cell temperature.
    This is a wrapper for the _read_temp function,
    with the device ID set with TEMP_SENSOR_ID_REF in the settings.py file.

    :return: Temperature of the reference cell in Celsius.
    """
    return await _read_temp(settings.TEMP_SENSOR_ID_REF)


async def read_temp_sample():
    """
    Reads sample cell temperature.
    This is a wrapper for the _read_temp function,
    with the device ID set with TEMP_SENSOR_ID_SAMPLE in the settings.py file.

    :return: Temperature of the sample cell in Celsius.
    """
    return await _read_temp(settings.TEMP_SENSOR_ID_SAMPLE)


async def _read_adc(channel, gain=1, scale=(1/185000.0)):
    """
    Reads measurement at a ADC channel with a specified GAIN.
    Converts the measurement mV into current in amps with a scaling factor.

    :param channel: channel number on the ADC device
    :param gain: factor of gain in ADC. No gain by default.
    :param scale: scale factor of the final output, by default converts mV into current in ampere.
    :return: ADC measurement.
    """
    global adc
    return adc.read_adc(channel, gain) * scale


async def read_current_ref():
    """An async wrapper function for reading realtime current at the reference."""
    return await _read_adc(settings.CURRENT_SENSOR_REF_CHANNEL)


async def read_current_sample():
    """An async wrapper function for reading realtime current at the sample."""
    return await _read_adc(settings.CURRENT_SENSOR_SAMPLE_CHANNEL)


async def measure_all(loop):
    """A convenience function to measure all readings with one concurrent Future object.

    :param loop: the main event loop.
    :returns: a tuple containing reference cell temp, sample cell temp, reference heater current, sample heater current.
    """
    _temp_ref, _temp_sample, _current_ref, _current_sample = await asyncio.gather(
        asyncio.ensure_future(read_temp_ref()),
        asyncio.ensure_future(read_temp_sample()),
        asyncio.ensure_future(read_current_ref()),
        asyncio.ensure_future(read_current_sample()),
        loop=loop)
    return _temp_ref, _temp_sample, _current_ref, _current_sample


def initialize():
    """Initial setup for GPIO board.
    Make all GPIO output pins set up as outputs.
    Start standby LED color (green).

    :returns A tuple of reference, sample PWM objects
    """

    if settings.SIMULATE_HARDWARE:
        print('GPIO board is all set up!')

        class FakePWM:
            """A fake PWM class with fake pwm-changing functionality for debugging."""
            def __init__(self, pin, frequency):
                self.pin = pin
                self.frequency = frequency
            def start(self, *args, **kwargs):
                pass
            def stop(self, *args, **kwargs):
                pass
            def ChangeDutyCycle(self, duty_cycle):
                print('Changed duty cycle on PIN {0} to {1}%'.format(self.pin, duty_cycle))


        class FakeADC:
            """A fake ADC voltage / current reader."""
            def __init__(self):
                pass
            def read_adc(self, channel, gain):
                return random.gauss(25, 2.0) * gain

        return FakePWM(settings.HEATER_REF_PIN, 1), FakePWM(settings.HEATER_SAMPLE_PIN, 1), FakeADC()

    GPIO.setmode(GPIO.BCM)
    GPIO.setup([settings.RED, settings.BLUE, settings.GREEN,
                settings.HEATER_REF_PIN, settings.HEATER_SAMPLE_PIN], GPIO.OUT)
    GPIO.output(settings.GREEN, GPIO.HIGH)

    heater_pwm_ref = GPIO.PWM(settings.HEATER_REF_PIN, 1)
    heater_pwm_sample = GPIO.PWM(settings.HEATER_SAMPLE_PIN, 1)
    adc_object = Adafruit_ADS1x15.ADS1115()
    return heater_pwm_ref, heater_pwm_sample, adc_object



def indicate_starting_up():
    """
    Indicate the device is heating to start_temp by turning on/off LED lights.
    """

    if settings.SIMULATE_HARDWARE:
        print('The Green LED has been switched on.')
        return

    GPIO.output((settings.GREEN, settings.RED), GPIO.LOW)
    GPIO.output(settings.BLUE, GPIO.HIGH)


def indicate_heating():
    """
    Indicate the device is heating in an active calorimetry by turning on/off LED lights.
    """

    if settings.SIMULATE_HARDWARE:
        print('The Red LED has been switched on.')
        return

    GPIO.output((settings.GREEN, settings.BLUE), GPIO.LOW)
    GPIO.output(settings.RED, GPIO.HIGH)


def cleanup():
    """
    Cleans up the whole GPIO board. Use when exception is raised.
    """

    if settings.SIMULATE_HARDWARE:
        print('GPIO board is cleaned up!')
        return

    GPIO.cleanup()
