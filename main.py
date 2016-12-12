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
import async_timeout
import logging
from hardware import (read_temp_ref, read_temp_sample, PID,
                      initialize, indicate_heating, indicate_starting_up, cleanup)
from utils import fetch, clamp, roughly_equal
import settings

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
    with async_timeout.timeout(settings.WEB_API_IDLE_INTERVAL):
        async with aiohttp.ClientSession(loop=loop) as session:
            payload = {
                'current_ref_temp': temp_ref,
                'current_sample_temp': temp_sample,
            }
            # fetch status information from web API
            data = await fetch(session, 'PUT', settings.WEB_API_STATUS_ADDRESS,
                               timeout=settings.WEB_API_IDLE_INTERVAL, **payload)

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

    # Check that
    if roughly_equal(temp_ref, temp_sample, active_job['start_temp'], tolerence=settings.TEMP_TOLERANCE):
        pass
    else:
        pass

    # Sleep for a set amount of time
    await asyncio.sleep(settings.TEMP_READ_TIME_INTERVAL)
    asyncio.ensure_future(idle(loop), loop=loop)


if __name__ == '__main__':

    try:
        # initialize the GPIO boards and set output pins to output mode
        initialize()

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

    except:
        # When any error occurs, it is important to clear all outputs on the GPIO board
        # so that the system does not keep heating up.
        cleanup()

        # re-raise the caught exception
        raise

    finally:
        # in case it doesn't run forever
        # also clean up at the end
        cleanup()

