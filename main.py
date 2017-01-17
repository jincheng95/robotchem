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
    Allow customisation of PID params, loop interval, maximum ramp rate from web interface.

Jin Cheng, 17/01/17
    Major refactor of common flow logic code into classes.
"""

import asyncio
import datetime
import inspect
import os
import sys

import aiohttp

from classes import Run, DataPoint
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

            if settings.DEBUG:
                print('****************************************'
                      '\nThe main event loop has entered the ACTIVE LOOP.')

            await active(loop, **data)

    # Run itself again
    asyncio.ensure_future(idle(loop), loop=loop)


async def active(_loop, **calorimeter_data):
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

    # Get a representation of this DSC run
    run = Run.from_web_resp(calorimeter_data, temp_ref, temp_sample)

    try:
        # Get cells to reach start temperature
        _loop.call_soon(indicate_starting_up)

        if settings.DEBUG:
            print('****************************************'
                  '\nThe main event loop has entered the GET READY LOOP.')

        await get_ready(_loop, run)

        # When control is yielded back from get_ready, start_temp has been reached
        _loop.call_soon(indicate_heating, _loop)

        if settings.DEBUG:
            print('****************************************'
                  '\nThe main event loop has entered the LINEAR RAMP LOOP.')
        await run_calorimetry(_loop, run)

    # when instructed to stop heating, clean up and return to idle function
    except StopHeatingError:
        cleanup(wipe=True)
        return


async def get_ready(_loop, run):
    """
    Gets the temperatures to starting temp as quickly as possible.

    :param _loop: the main event loop.
    :param run: the object representing the run params.
    """

    # Make available the heater PWM objects, then asynchronously measure temperatures
    run.heater_ref.start(0), run.heater_sample.start(0)
    run.last_time = _loop.time()

    while True:
        # Measure all data
        await run.make_measurement(_loop)

        # if start temp is reached, give back control to whichever coroutine that called it
        # but if sample hasn't been inserted, keep holding at start temp and keep running this loop
        if run.is_ready and run.check_stabilization(run.start_temp):
            break

        # Watch web API response for whether user has put in the sample
        run.is_ready = await run.upload_queue(_loop)

        # Sleep for a set amount of time, then rerun the PWM calculations
        await asyncio.sleep(run.interval)


async def run_calorimetry(_loop, run):
    """An async function that starts the heat ramp until the end temp is reached at the rate of choice.
    Periodically and transmit currents and temperatures to web API.

    :param _loop: the main event loop
    :param run: the object representing the run params.
    """

    run.last_time = _loop.time()
    set_point = run.start_temp
    while True:
        # make measurements and upload
        await run.make_measurement(_loop)
        await run.upload_queue(_loop)

        # if current temps are more or less the desired set point, increment the ramp
        if run.check_stabilization(set_point, duration=2):
            set_point += run.real_ramp_rate
        await asyncio.sleep(run.interval)


if __name__ == '__main__':
    # initialize the GPIO boards and set output pins to output mode
    initialize(board_only=True)

    # asynchronous main event loop
    loop = asyncio.get_event_loop()

    # enable verbose mode if in development
    if settings.DEBUG:
        loop.set_debug(enabled=True)

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
