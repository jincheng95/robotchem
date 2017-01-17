"""
Classes to generalise common patterns with DSC data.
Has some similarities to the database models on the web backend.

Jin Cheng, 17/01/17
"""
import datetime

from hardware import measure_all, PID, initialize
from utils import NetworkQueue, clamp, roughly_equal, batch_upload
import settings


class Run(object):
    """An object loosely based on the backend database model `Run` with additional hardware properties
    such as the PID object, the Analog-to-digital object, and the Network upload queue."""

    def __init__(self, run_id, start_temp, target_temp, ramp_rate,
                 PID_ref, PID_sample, interval, min_upload_length, stabilization_duration,
                 temp_tolerance=1):
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
        :param loop: The main event loop.
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
        pids = self.PID_ref, self.PID_sample
        temps = measurement.temp_ref, measurement.temp_sample
        duty_cycles = self.duty_cycle_ref, self.duty_cycle_sample

        # batch change duty cycles based on calculated outputs
        heaters = self.heater_ref, self.heater_sample
        for pid, temp, duty_cycle, heater in zip(pids, temps, duty_cycles, heaters):
            duty_cycle = clamp(pid.update(temp))
            _loop.call_soon(heater.ChangeDutyCycle, duty_cycle)

        return measurement

    async def upload_queue(self, _loop):
        """Checks if the network queue has crossed the threshold to upload data."""
        self.is_ready = await batch_upload(_loop, self)
        return self.is_ready

    def batch_setpoint(self, setpoint):
        for pid in (self.PID_sample, self.PID_ref):
            pid.set_setpoint(setpoint)

    def check_stabilization(self, value, duration=None, tolerance_factor=1):
        """
        Check if the temperatures of the last measurements are within range of the value.
        The measurements must be made within a specified amount of time ago and
        the temperature comparison tolerance is also customisable.
        :return: Whether stabilisation at start temperature has been achieved.
        """
        self.stabilized_at_start = False
        if len(self.data_points) == 0:
            return self.stabilized_at_start

        # first, a quick check to see if very last measurement is very out of start temp range
        last_data_point = self.data_points[-1]
        if not roughly_equal(last_data_point.temp_ref, last_data_point.temp_sample, value, tolerence=3):
            if settings.DEBUG:
                print('The run has not stabilised at {v} from a rough check on the last set of '
                      'temperature measurement.'.format(v=value))
            return self.stabilized_at_start

        count = 0
        duration = duration or self.stabilization_duration

        # check if temps in recent measurements reached within a certain range around start_temp
        now = datetime.datetime.now()
        for point in reversed(self.data_points):
            seconds_passed = (now - point.measured_at).total_seconds()
            # if within time limit and previous result are true
            if seconds_passed <= duration and (self.stabilized_at_start or count == 0):
                count += 0
                self.stabilized_at_start = roughly_equal(point.temp_ref, point.temp_sample,
                                                         value, tolerence=self.temp_tolerance * tolerance_factor)
                if settings.DEBUG:
                    print("{count}: {result}".format(count=count, result=self.stabilized_at_start))
            elif seconds_passed > duration + self.stabilization_duration:
                break
        return self.stabilized_at_start

    @property
    def real_ramp_rate(self):
        return self.ramp_rate * settings.MAX_RAMP_RATE

    @classmethod
    def from_web_resp(cls, json_data, temp_ref, temp_sample):
        """
        Construct a Run object from a dictionary of returned values from the web status API page.
        :param json_data: Returned JSON response.
        :param temp_ref: Measured temperature at ref.
        :param temp_sample: Measured temperature at sample
        :return: This object.
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
                   json_data.get('stabilization_duration') or settings.TEMP_STABILISATION_MIN_DURATION)


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
        """Construct a new DataPoint object based a new, raw measurement."""
        temp_ref, temp_sample, current_ref, current_sample = await measure_all(loop, run.adc)

        voltage_ref = settings.MAX_VOLTAGE * run.duty_cycle_ref / 100
        voltage_sample = settings.MAX_VOLTAGE * run.duty_cycle_sample / 100
        heat_ref = voltage_ref * current_ref * delta_time
        heat_sample = voltage_sample * current_sample * delta_time

        return cls(run, datetime.datetime.now(),
                   temp_ref, temp_sample, heat_ref, heat_sample)
