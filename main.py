"""
Main script to be run automatically on raspberry Pi startup.
Web requests, measurements and GPIO control occur simultaneously and independently.
Concurrency based on Python 3.5's async/await syntax with the asyncio library.

Hayley Weir, 11/12/16:
    Hardware (GPIO control),
    PID calculation,
    Heat ramp process

Jin Cheng, 12/12/16:
    Asynchronous functions, event loops, futures and coroutines,
    Web API communication,
    Calorimetry and flow logic,
    Implement current -> power -> energy conversion,
    Documentation

Jin Cheng, 16/01/17:
    Several debugging changes to simplify calibration,
    Allow customisation of PID params, loop interval, maximum ramp rate from web interface
"""

import asyncio
import datetime
import inspect
import os
import sys

import aiohttp

import settings
from hardware import (read_temp_ref, read_temp_sample, measure_all, PID,
                      initialize, indicate_heating, indicate_starting_up, cleanup)
from utils import fetch, clamp, roughly_equal, batch_upload, StopHeatingError, NetworkQueue
import logging

# For some reason, relative imports on the raspberry pi do not work unless the following is included
ROOT_DIR = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


async def idle(loop):
    """
    An asynchronous coroutine run periodically during idle periods.
    Checks the web API if it should new jobs, and updates the web API about current temperatures.

    :param loop: The main event loop.
    """

    # Read temperatures simultaneously by creating a combined Future object (blocking)
    temp_ref, temp_sample = await asyncio.gather(asyncio.ensure_future(read_temp_ref()),
                                                 asyncio.ensure_future(read_temp_sample()),
                                                 loop=loop)

    # Provide periodic updates to the Idle Web API about its current temperature
    async with aiohttp.ClientSession(loop=loop) as session:
        payload = {
            'current_ref_temp': temp_ref,
            'current_sample_temp': temp_sample,
        }
        # fetch status information from web API
        data = await fetch(session, 'PUT', settings.WEB_API_STATUS_ADDRESS,
                           timeout=settings.WEB_API_IDLE_INTERVAL, payload=payload)

    if settings.DEBUG:
        print(data)

    # Check if user has instructed a new run
    if 'has_active_runs' in data:
        active_run = data['has_active_runs']

        if isinstance(active_run, bool) and not active_run:
            # Sleep for a set interval determined in settings.py
            # so this can be refreshed later
            await asyncio.sleep(data.get('idle_loop_interval') or settings.WEB_API_IDLE_INTERVAL)

        elif isinstance(active_run, dict):
            # pass the active run information to the active function,
            # wait for the active run to finish
            # and return control to the idle function.
            await active(loop, active_run, **data)

    # Run itself again
    asyncio.ensure_future(idle(loop), loop=loop)


async def active(_loop, active_job, **calorimter_data):
    """
    An asynchronous coroutine run periodically during an active calorimetry job.
    Contains logic about the set point, heating to start temp as quickly as possible, and uploading measurements.
    Periodically calculates PID numbers.

    :param _loop: The main event loop.
    :param active_job: Dictionary, containing information regarding the active job,
    returned as a response from the web API.
    """

    # Read temperatures simultaneously by creating a combined Future object (blocking)
    temp_ref, temp_sample = await asyncio.gather(asyncio.ensure_future(read_temp_ref()),
                                                 asyncio.ensure_future(read_temp_sample()),
                                                 loop=_loop)
    start_temp, run_id = active_job['start_temp'], active_job['id']

    # Create a network data queue
    active_loop_interval = calorimter_data.get('active_loop_interval') or settings.WEB_API_ACTIVE_INTERVAL
    min_upload_length = calorimter_data.get('web_api_min_upload_length') or settings.WEB_API_MIN_UPLOAD_LENGTH
    network_queue = NetworkQueue(threshold_time=active_loop_interval, threshold_qsize=min_upload_length)

    # Instantiate new PID objects
    pid_init_kwargs = {
        'set_point': start_temp,
        'Kp': calorimter_data.get('K_p'),
        'Ki': calorimter_data.get('K_i'),
        'Kd': calorimter_data.get('K_d'),
    }
    pid_ref, pid_sample = PID(temp_ref, **pid_init_kwargs), PID(temp_sample, **pid_init_kwargs)

    try:
        # Get cells to reach start temperature
        _loop.call_soon(indicate_starting_up)
        await get_ready(_loop, pid_ref, pid_sample, network_queue, run_id, active_loop_interval)

        # When control is yielded back from get_ready, start_temp has been reached
        _loop.call_soon(indicate_heating)
        await run_calorimetry(_loop, active_job, network_queue, run_id, active_loop_interval)

    # when instructed to stop heating, clean up and return to idle function
    except StopHeatingError:
        cleanup()
        return


async def get_ready(_loop, pid_ref, pid_sample, network_queue, run_id, interval):
    """
    Gets the temperatures to starting temp as quickly as possible.

    :param _loop: the main event loop.
    :param pid_ref: the PID object for the reference cell. This is spawned in the `active` coroutine.
    :param pid_sample: the PID object for the sample cell. This is spawned in the `active` coroutine.
    :param network_queue: the NetworkQueue object with which this function spawns a consumer thread
    that transmits the data in the queue and produces data items in the queue.
    :param run_id: unique numeric ID from web API of this particular run.
    :param interval: (minimum) time interval between each cycle of PID calculation.
    """

    # Make available the heater PWM objects, then asynchronously measure temperatures
    global heater_ref, heater_sample, adc
    heater_ref.start(0), heater_sample.start(0)

    last_time = _loop.time()
    sample_inserted = False
    while True:
        # Measure all data
        temp_ref, temp_sample, current_ref, current_sample = await measure_all(_loop, adc)

        # if start temp is reached, give back control to whichever coroutine that called it
        # but if sample hasn't been inserted, keep holding at start temp and keep running this loop
        if roughly_equal(temp_ref, temp_sample, pid_ref.set_point, tolerence=settings.TEMP_TOLERANCE) \
                and sample_inserted:
            break

        # Set set_point straight to start_temp to heat as quickly as possible
        # Then change PWM
        duty_cycle_ref = clamp(pid_ref.update(temp_ref))
        duty_cycle_sample = clamp(pid_sample.update(temp_sample))

        # Change PWM as soon as possible
        _loop.call_soon(heater_ref.ChangeDutyCycle, duty_cycle_ref)
        _loop.call_soon(heater_sample.ChangeDutyCycle, duty_cycle_sample)

        # calculate time and time deltas
        now = _loop.time()
        delta_time = now - last_time
        last_time = now

        # calculate power, record current time
        voltage_ref = settings.MAX_VOLTAGE * duty_cycle_ref / 100
        voltage_sample = settings.MAX_VOLTAGE * duty_cycle_sample / 100
        heat_ref = voltage_ref * current_ref * delta_time
        heat_sample = voltage_sample * current_sample * delta_time

        # Send payload to network comms queue
        payload = {
            'run': run_id,
            'measured_at': datetime.datetime.now().isoformat(sep='T'),
            'temp_ref': temp_ref,
            'temp_sample': temp_sample,
            'heat_ref': heat_ref,
            'heat_sample': heat_sample,
        }
        await network_queue.put(payload)

        # Watch web API response for whether user has put in the sample
        sample_inserted = await batch_upload(_loop, network_queue, run_id)

        # Sleep for a set amount of time, then rerun the PWM calculations
        await asyncio.sleep(interval)


async def run_calorimetry(_loop, active_job, network_queue, run_id, interval):
    """An async function that starts the heat ramp until the end temp is reached at the rate of choice.
    Periodically and transmit currents and temperatures to web API.

    :param _loop: the main event loop
    :param active_job: the active job dict object from the web API
    :param network_queue: the NetworkQueue object with which this function spawns a consumer thread
    that transmits the data in the queue and produces data items in the queue.
    :param run_id: unique numeric ID from web API of this particular run.
    :param interval: (minimum) time interval between each cycle of PID calculation.
    """

    # Get heater PWM objects
    global heater_ref, heater_sample, adc
    heater_ref.start(0), heater_sample.start(0)

    # Make local variables based on job params
    start_temp, end_temp, rate = (active_job['start_temp'], active_job['target_temp'],
                                  active_job['ramp_rate'] * settings.MAX_RAMP_RATE,
                                  )

    # Instantiate new PID objects
    pid_ref, pid_sample = (PID(await read_temp_ref(), set_point=start_temp),
                           PID(await read_temp_sample(), set_point=start_temp))

    last_time = _loop.time()
    set_point = start_temp
    while True:
        temp_ref, temp_sample, current_ref, current_sample = await measure_all(_loop, adc)

        # calculate PID-controlled PWM and change duty cycle accordingly
        duty_cycle_ref = clamp(pid_ref.update(temp_ref))
        duty_cycle_sample = clamp(pid_sample.update(temp_sample))
        heater_ref.ChangeDutyCycle(duty_cycle_ref)
        heater_sample.ChangeDutyCycle(duty_cycle_sample)

        # calculate time and time deltas
        now = _loop.time()
        delta_time = now - last_time
        last_time = now

        # calculate power, record current time and send payload to network comms queue
        voltage_ref = settings.MAX_VOLTAGE * duty_cycle_ref / 100
        voltage_sample = settings.MAX_VOLTAGE * duty_cycle_sample / 100
        heat_ref = voltage_ref * current_ref * delta_time
        heat_sample = voltage_sample * current_sample * delta_time

        payload = {
            'run': run_id,
            'measured_at': datetime.datetime.now().isoformat(sep='T'),
            'temp_ref': temp_ref,
            'temp_sample': temp_sample,
            'heat_ref': heat_ref,
            'heat_sample': heat_sample,
        }
        await network_queue.put(payload)
        await batch_upload(_loop, network_queue, run_id)

        # if current temps are more or less the desired setpoint, increment the ramp
        if roughly_equal(temp_ref, temp_sample, set_point, tolerence=settings.TEMP_TOLERANCE) \
                and set_point < end_temp:
            set_point += rate
        await asyncio.sleep(interval)


if __name__ == '__main__':
    # initialize the GPIO boards and set output pins to output mode
    heater_ref, heater_sample, adc = initialize()

    # asynchronous main event loop
    loop = asyncio.get_event_loop()

    # enable verbose mode if in development
    if settings.DEBUG:
        loop.set_debug(enabled=True)
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        logging.getLogger('asyncio').setLevel(logging.DEBUG)

    try:
        # start and run main event loop
        asyncio.ensure_future(idle(loop), loop=loop)
        loop.run_forever()

    finally:
        # When any error occurs or when the main loop ends,
        # it is important to clear all outputs on the GPIO board
        # so that the system does not keep heating up.
        cleanup(wipe=True)
        loop.stop()
        loop.close()
