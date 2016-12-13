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
    Documentation
"""

import asyncio
import aiohttp
import datetime

from hardware import (read_temp_ref, read_temp_sample, read_current_ref, read_current_sample, measure_all, PID,
                      initialize, indicate_heating, indicate_starting_up, cleanup)
from utils import fetch, clamp, roughly_equal, batch_upload, SampleNotInsertedError, StopHeatingError, NetworkQueue
import settings

if settings.DEBUG:
    import logging


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
            await asyncio.sleep(settings.WEB_API_IDLE_INTERVAL)

        elif isinstance(active_run, dict):
            # pass the active run information to the active function,
            # wait for the active run to finish
            # and return control to the idle function.
            await active(loop, active_run)

    # Run itself again
    asyncio.ensure_future(idle(loop), loop=loop)


async def active(loop, active_job):
    """
    An asynchronous coroutine run periodically during an active calorimetry job.
    Contains logic about the set point, heating to start temp as quickly as possible, and uploading measurements.
    Periodically calculates PID numbers.

    :param loop: The main event loop.
    :param active_job: Dictionary, containing information regarding the active job,
    returned as a response from the web API.
    """

    # Read temperatures simultaneously by creating a combined Future object (blocking)
    temp_ref, temp_sample = await asyncio.gather(asyncio.ensure_future(read_temp_ref()),
                                                 asyncio.ensure_future(read_temp_sample()),
                                                 loop=loop)
    start_temp, run_id = active_job['start_temp'], active_job['id']

    # Create a network data queue
    network_queue = NetworkQueue()

    # Instantiate new PID objects and get cells to reach start temperature
    pid_ref, pid_sample = PID(temp_ref, set_point=start_temp), PID(temp_sample, set_point=start_temp)
    loop.call_soon(indicate_starting_up)

    async def get_ready_wrapper():
        try:
            return await get_ready(loop, pid_ref, pid_sample, network_queue, run_id)
        except SampleNotInsertedError:
            get_ready_wrapper()
    await get_ready_wrapper()

    # When control is yielded back from get_ready, start_temp has been reached
    loop.call_soon(indicate_heating)
    try:
        await run_calorimetry(loop, active_job, network_queue, run_id)
    except StopHeatingError:
        # when instructed to stop heating, clean up and return to idle function
        cleanup()
        return


async def get_ready(loop, pid_ref, pid_sample, network_queue, run_id):
    """Gets the temperatures to starting temp as quickly as possible."""

    # Make available the heater PWM objects, then asynchronously measure temperatures
    global heater_ref, heater_sample
    heater_ref.start(0), heater_sample.start(0)

    last_time = loop.time()
    while True:
        # Measure all data
        temp_ref, temp_sample, current_ref, current_sample = await measure_all(loop)

        # if start temp is reached, give back control to whichever coroutine that called it
        if roughly_equal(temp_ref, temp_sample, pid_ref.set_point, tolerence=settings.TEMP_TOLERANCE):
            break

        # Set set_point straight to start_temp to heat as quickly as possible
        # Then change PWM
        duty_cycle_ref = clamp(pid_ref.update(temp_ref))
        duty_cycle_sample = clamp(pid_sample.update(temp_sample))

        # Change PWM as soon as possible
        loop.call_soon(heater_ref.ChangeDutyCycle, duty_cycle_ref)
        loop.call_soon(heater_sample.ChangeDutyCycle, duty_cycle_sample)

        # calculate time and time deltas
        now = loop.time()
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
        await batch_upload(loop, network_queue, run_id)

        # Sleep for a set amount of time, then rerun the PWM calculations
        await asyncio.sleep(settings.MAIN_LOOP_INTERVAL)


async def run_calorimetry(loop, active_job, network_queue, run_id):

    # Get heater PWM objects
    global heater_ref, heater_sample

    # Make local variables based on job params
    start_temp, end_temp, rate = (active_job['start_temp'], active_job['target_temp'],
                                  active_job['ramp_rate'] * settings.MAX_RAMP_RATE,
                                  )

    # Instantiate new PID objects
    pid_ref, pid_sample = (PID(await read_temp_ref(), set_point=start_temp),
                           PID(await read_temp_sample(), set_point=start_temp))

    last_time = loop.time()
    set_point = start_temp
    while True:
        temp_ref, temp_sample, current_ref, current_sample = await measure_all(loop)

        # calculate PID-controlled PWM and change duty cycle accordingly
        duty_cycle_ref = clamp(pid_ref.update(temp_ref))
        duty_cycle_sample = clamp(pid_sample.update(temp_sample))
        heater_ref.ChangeDutyCycle(duty_cycle_ref)
        heater_sample.ChangeDutyCycle(duty_cycle_sample)

        # calculate time and time deltas
        now = loop.time()
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
        await batch_upload(loop, network_queue, run_id)

        # if current temps are more or less the desired setpoint, increment the ramp
        if roughly_equal(temp_ref, temp_sample, set_point, tolerence=settings.TEMP_TOLERANCE) \
                and set_point < end_temp:
            set_point += rate
        await asyncio.sleep(settings.MAIN_LOOP_INTERVAL)


if __name__ == '__main__':
    try:
        # initialize the GPIO boards and set output pins to output mode
        heater_ref, heater_sample = initialize()

        # asynchronous main event loop
        loop = asyncio.get_event_loop()

        # enable verbose mode if in development
        if settings.DEBUG:
            loop.set_debug(enabled=True)
            logging.getLogger('asyncio').setLevel(logging.DEBUG)

        # start idle loop
        asyncio.ensure_future(idle(loop), loop=loop)

        # run forever and ever, and ever...
        loop.run_forever()

    finally:
        # When any error occurs or when the main loop ends,
        # it is important to clear all outputs on the GPIO board
        # so that the system does not keep heating up.
        cleanup()
