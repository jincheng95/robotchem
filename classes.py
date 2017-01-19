"""
Classes to generalise common patterns with DSC data.
Has some similarities to the database models on the web backend.

Jin Cheng, 17/01/17:
    Wrote these classes partly using existing code from `main.py`.

Jin Cheng, 18/01/17:
    Further simplification of the Run object.
"""
import asyncio
import datetime
import time

import aiohttp

from robotchem import settings
from robotchem.hardware import measure_all, PID, initialize
from robotchem.utils import NetworkQueue, clamp, roughly_equal, fetch, StopHeatingError


class Run(object):
    """An object loosely based on the backend database model `Run` with additional hardware properties
    such as the PID object, the Analog-to-digital object, and the Network upload queue."""

    def __init__(self, run_id, start_temp, target_temp, ramp_rate,
                 PID_ref, PID_sample, interval, min_upload_length, stabilization_duration,
                 temp_tolerance):
        """
        Generic init method that initiates the class.

        :type run_id: int
        :param run_id: Run ID from the web server response.
        :type start_temp: float
        :param start_temp: Starting temperature specified by the user on the web interface.
        :type target_temp: float
        :param target_temp: Target temperature specified by the user on the web interface.
        :type ramp_rate: float
        :param ramp_rate: Ramp rate (0 - 1), as fraction of max rate, specified by the user on the web interface.
        :type PID_ref: hardware.PID
        :param PID_ref: PID object for the reference heater
        :type PID_sample: hardware.PID
        :param PID_sample: PID object for the sample heater
        :type interval: float
        :param interval: Main event PID calculation refresh interval.
        :type min_upload_length: int
        :param min_upload_length: Minimum number of measurements in batches when uploading data.
        :type stabilization_duration: float
        :param stabilization_duration: Minimum duration, in seconds, that temperature must stabilise before moving on.
        :type temp_tolerance: float
        :param temp_tolerance: Maximum difference between two temperature readings, in degrees Celsius,
        for them to be considered equivalent.
        """
        self.id = run_id
        self.start_temp = start_temp
        self.target_temp = target_temp
        self.ramp_rate = ramp_rate

        self.PID_ref = PID_ref
        self.PID_sample = PID_sample

        self.heater_ref, self.heater_sample, self.adc = initialize()
        self.duty_cycle_ref, self.duty_cycle_sample = 0, 0

        self.interval = interval
        self.min_upload_length = min_upload_length
        self.temp_tolerance = temp_tolerance
        self.stabilization_duration = stabilization_duration

        self.stabilized_at_start = False
        self.is_ready = False
        self.is_finished = False

        self.last_time = -1
        self.network_queue = NetworkQueue(threshold_time=interval, threshold_qsize=min_upload_length)
        self.data_points = []

    async def make_measurement(self, _loop):
        """
        Make a new measurement asynchronously and store it to the series of measurements related to this run.
        All measurements are put into the network queue responsible for this run's data.

        Temperature measurements made are automatically fed into the :class:`robotchem.hardware.PID`
        objects related to this run.
        The main event loop is used to change the duty cycle on the respective heater PWM objects,
        :class:`RPi.GPIO.PWM`.

        :type _loop: asyncio.BaseEventLoop
        :param _loop: The main event loop.
        :rtype: robotchem.classes.DataPoint
        :return: The DataPoint object, containing all measurements made and measurement time.
        """

        # calculate time and time deltas
        now = _loop.time()
        delta_time = now - self.last_time
        self.last_time = now

        # make new data point by new measurements
        measurement = await DataPoint.async_measure_raw(self, _loop, delta_time)
        self.data_points.append(measurement)

        # send its json representation into the upload queue
        await self.network_queue.put(measurement.jsonify())

        # batch update pid values
        self.duty_cycle_ref = clamp(self.PID_ref.update(measurement.temp_ref))
        self.duty_cycle_sample = clamp(self.PID_sample.update(measurement.temp_sample))

        # batch change duty cycles based on calculated outputs
        _loop.call_soon(self.heater_ref.ChangeDutyCycle, self.duty_cycle_ref)
        _loop.call_soon(self.heater_sample.ChangeDutyCycle, self.duty_cycle_sample)

        return measurement

    async def queue_upload(self, _loop, override_threshold=None):
        """An asynchronous function that uploads payloads by consuming from the network queue
        only when a specified amount of time has passed from time of last processing
        and when a specified number of items exist in the queue.
        The asynchronous process breaks otherwise.

        :type _loop: asyncio.BaseEventLoop
        :param _loop: the main event loop
        :type override_threshold: bool
        :param override_threshold: whether qsize and delta time constraints for batch uploading should be overrode
        :rtype: bool
        :returns: if sample has been inserted and formal temp ramp can begin

        :exception StopHeatingError: When this error is raised, any async function that calls it must give control \
        back to the idle loop and stop heating. Raised if a 'stop_flag' field returns True from the web API response.
        """
        while True:
            # Only make HTTP requests above certain item number threshold
            # and after a set amount of time since last upload
            q, qsize = self.network_queue, self.network_queue.qsize()

            if override_threshold or (
                    qsize() >= q.threshold_qsize and (time.time() - q.last_time) >= q.threshold_time):

                # collect all items in the queue
                data = await asyncio.gather(
                    *[asyncio.ensure_future(q.get()) for _ in range(q.qsize())],
                    loop=_loop
                )

                # make the request and clear the local waiting list
                payload = {
                    'data': data,
                    'run': self.id,
                    'stabilized_at_start': self.stabilized_at_start,
                    'is_finished': self.is_finished,
                }
                async with aiohttp.ClientSession(loop=_loop) as session:
                    response = await fetch(session, 'POST', settings.WEB_API_DATA_ADDRESS, payload=payload)
                if settings.DEBUG:
                    print(response)

                # reset network queue last processed time
                q.last_time = time.time()

                # Check for stop heating and sample inserted flags from the web API
                if response.get('stop_flag'):
                    raise StopHeatingError
                self.is_ready = response.get('is_ready')
                return self.is_ready
            else:
                break

    def batch_setpoint(self, setpoint):
        """
        Changes the set point for both PID objects related to the run's sample and reference cells.

        :type setpoint: int
        :param setpoint: temperature in Celsius.
        """
        setpoint = clamp(setpoint, 0, self.target_temp)
        for pid in (self.PID_sample, self.PID_ref):
            pid.set_setpoint(setpoint)

    def check_stabilization(self, value, duration=None, tolerance=None):
        """
        Check if the latest temperatures are within range of the ``value`` given. \
        The measurements must be made within a specified amount of time ago and \
        the temperature comparison tolerance is also customisable.

        :type value: float | int
        :param value: value around which to determine if temperatures have stabilised

        :type duration: float | int
        :param duration: value with which to override this object's stabilisation duration constraint, \
            :const:`self.stabilization_duration`

        :type: tolerance: float | int
        :param tolerance: value with which to override this object's temperature tolerance, \
            :const:`self.temp_tolerance`

        :rtype: bool
        :return: Whether stabilisation at the specified temperature has been achieved.
        """
        has_stabilized = False

        # return False if no measurements have been made
        if len(self.data_points) == 0:
            return False

        # first, a quick check to see if very last measurement is very out of start temp range
        # hopefully this reduces computation time
        last_data_point = self.data_points[-1]
        if not roughly_equal(last_data_point.temp_ref, last_data_point.temp_sample, value, tolerence=3):
            if settings.DEBUG:
                print('The run has not stabilised at {v} from a rough check on the last set of '
                      'temperature measurement.'.format(v=value))
            return has_stabilized

        # if last measurement within range of 3, check series of recently made values
        has_stabilized = True
        duration = duration or self.stabilization_duration
        tolerance = tolerance or self.temp_tolerance

        # check if temps in recent measurements reached within a certain range around start_temp
        now = datetime.datetime.now()
        for point in reversed(self.data_points):
            seconds_passed = (now - point.measured_at).total_seconds()

            # if within time limit
            if seconds_passed <= duration:
                has_stabilized = has_stabilized and \
                                 roughly_equal(point.temp_ref, point.temp_sample,
                                               value, tolerence=tolerance)
                if settings.DEBUG:
                    print("{seconds}s: {result}".format(seconds=seconds_passed, result=has_stabilized))

            elif seconds_passed > duration + self.stabilization_duration:
                break
        return has_stabilized

    @property
    def real_ramp_rate(self):
        """
        Calculate the real temperature increment per main loop cycle, in degrees Celsius.
        The `ramp_rate` field is selected by the user on the web interface and
        the `self.ramp_rate` property stores the percentage of the maximum available ramp rate.

        :rtype: float
        :return: Temperature increase per cycle, in degrees Celsius.
        """
        return self.ramp_rate * settings.MAX_RAMP_RATE

    @classmethod
    def from_web_resp(cls, json_data, temp_ref, temp_sample):
        """
        Construct a Run object from a dictionary of returned values from the web status API page.
        PID objects are instantiated with initial temperature values supplied.
        The customisable parameters from the web API are also stored,
        and if none is given, defaults from :mod:`robotchem.settings` will be used.

        :param json_data: Returned JSON response.
        :param temp_ref: Measured temperature at ref.
        :param temp_sample: Measured temperature at sample
        :return: A :class:`robotchem.classes.Run` object.
        """
        run_data = json_data['has_active_runs']

        PID_init_kwargs = {
            'Kp': json_data['K_p'],
            'Ki': json_data['K_i'],
            'Kd': json_data['K_d'],
            'set_point': run_data['start_temp']
        }
        PID_ref = PID(temp_ref, **PID_init_kwargs)
        PID_sample = PID(temp_sample, **PID_init_kwargs)

        return cls(run_data['id'], run_data['start_temp'], run_data['target_temp'], run_data['ramp_rate'],
                   PID_ref, PID_sample,
                   json_data.get('active_loop_interval') or settings.MAIN_LOOP_INTERVAL,
                   json_data.get('web_api_min_upload_length') or settings.WEB_API_MIN_UPLOAD_LENGTH,
                   json_data.get('stabilization_duration') or settings.TEMP_STABILISATION_MIN_DURATION,
                   json_data.get('temp_tolerance_range') or settings.TEMP_TOLERANCE)


class DataPoint(object):
    """An object based on the web backend database model `DataPoint`."""

    def __init__(self, run, measured_at, temp_ref, temp_sample, heat_ref, heat_sample):
        self.run = run
        self.measured_at = measured_at

        self.temp_ref = temp_ref
        self.temp_sample = temp_sample
        self.heat_ref = heat_ref
        self.heat_sample = heat_sample

    def jsonify(self):
        """Pickle properties of this object into a JSON-ifiable dictionary. For communications with the web interface.

        :rtype: dict
        :return: dictionary representation of this object's properties.
        """
        res = {
            'run': self.run.id,
            'measured_at': self.measured_at.isoformat(sep='T'),
            'temp_ref': self.temp_ref,
            'temp_sample': self.temp_sample,
            'heat_ref': self.heat_ref,
            'heat_sample': self.heat_sample,
        }
        return res

    @classmethod
    async def async_measure_raw(cls, run, loop, delta_time):
        """Construct a new DataPoint object based a new, raw measurement.

        :type run: `robotchem.classes.Run`
        :param run: parent `Run` object.
        :type loop: asyncio.BaseEventLoop
        :param loop: main event loop.
        :type delta_time: float
        :param delta_time: time, in seconds, passed since last measurement (i.e. construction \
        of previous instance of this class related to the `Run`)
        :return: `robotchem.classes.DataPoint` object.
        """
        temp_ref, temp_sample, current_ref, current_sample = await measure_all(loop, run.adc)

        voltage_ref = settings.MAX_VOLTAGE * run.duty_cycle_ref / 100
        voltage_sample = settings.MAX_VOLTAGE * run.duty_cycle_sample / 100
        heat_ref = voltage_ref * current_ref * delta_time
        heat_sample = voltage_sample * current_sample * delta_time

        return cls(run, datetime.datetime.now(),
                   temp_ref, temp_sample, heat_ref, heat_sample)
