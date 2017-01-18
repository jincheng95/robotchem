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

Jin Cheng, 17/01/17:
    Major refactor of common flow logic code into classes,
    Optimisation of the temperature ramp logic to linearise temp profile as much as possible.
"""

import asyncio
import inspect
import os
import sys

import aiohttp

import settings
from classes import Run
from hardware import (read_temp_ref, read_temp_sample, initialize, indicate_heating, indicate_starting_up, cleanup)
from utils import fetch, StopHeatingError


async def idle(_loop):
    """
    An asynchronous coroutine run periodically during idle periods.
    Checks the web API if it should new jobs, and updates the web API about current temperatures.

    :param _loop: The main event loop.
    """

    # Read temperatures simultaneously by creating a combined Future object (blocking)
    temp_ref, temp_sample = await asyncio.gather(asyncio.ensure_future(read_temp_ref()),
                                                 asyncio.ensure_future(read_temp_sample()),
                                                 loop=_loop)

    # Provide periodic updates to the Idle Web API about its current temperature
    async with aiohttp.ClientSession(loop=_loop) as session:
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

            await active(_loop, **data)

    # Run itself again
    asyncio.ensure_future(idle(_loop), loop=_loop)


async def active(_loop, **calorimeter_data):
    """
    An asynchronous coroutine run periodically during an active calorimetry job.
    Contains logic about the set point, heating to start temp as quickly as possible, and uploading measurements.
    Periodically calculates PID numbers.

    :param _loop: The main event loop.
    :param calorimeter_data: JSON representation of the active job from the server API.
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
        cleanup(run.heater_sample, run.heater_ref, wipe=True)
        initialize(board_only=True)
        return


async def get_ready(_loop, run):
    """
    An aync function that gets the temperatures to starting temp as quickly as possible.

    :param _loop: the main event loop.
    :param run: the object representing the run params.
    """

    # Make available the heater PWM objects, then asynchronously measure temperatures
    run.heater_ref.start(0), run.heater_sample.start(0)
    run.last_time = _loop.time()

    while True:
        # Measure all data then upload
        await run.make_measurement(_loop)
        await run.queue_upload(_loop)

        # if start temp is reached, give back control to whichever coroutine that called this function
        # but if sample hasn't been inserted, keep holding at start temp and keep running this loop
        run.stabilized_at_start = run.check_stabilization(run.start_temp)
        if run.is_ready and run.stabilized_at_start:
            break

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
        await run.queue_upload(_loop)

        # use a less stringent check (higher value tolerance and smaller duration) to make linear the temp profile
        stabilised_at_setpoint= run.check_stabilization(set_point, duration=2, tolerance=1.25 * run.real_ramp_rate)

        # if current temps are more or less the desired set point, increment the ramp
        if stabilised_at_setpoint:
            set_point += run.real_ramp_rate
            run.batch_setpoint(set_point)

            if settings.DEBUG:
                print("*********************************\n"
                      "The setpoint has been increased to {setpoint}".format(setpoint=set_point))

        # check if temp has stabilised near the end temp and change its status accordingly
        if (not run.is_finished) and run.check_stabilization(run.target_temp, duration=50):
            run.is_finished = True
            # upload this status and rest of the data
            await run.queue_upload(_loop, override_threshold=True)
            raise StopHeatingError

        # Sleep for a set amount of time, then rerun the PWM calculations
        await asyncio.sleep(run.interval)


if __name__ == '__main__':
    # For some reason, some imports on the raspberry pi do not work unless the following is included
    ROOT_DIR = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)

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
