"""
Utility functions and classes for common calculations and networking patterns.

Jin Cheng 12/12/16
"""

import asyncio
import json
import time
from itertools import combinations

import aiohttp
import async_timeout

import settings


class StopHeatingError(BaseException):
    """An exception, when raised, should stop heating in cells
    and terminate current active calorimetry job."""
    pass


async def fetch(session, method, url, payload, timeout=settings.WEB_API_ACTIVE_INTERVAL, **kwargs):
    """
    An asynchronous HTTP request function sending JSON data,
    with an automatically included ACCESS_CODE field from settings.py.

    :param session: the async HTTP session content manager
    :param method: method of the HTTP request
    :param url: URL of the API endpoint
    :param timeout: raise a time out error after this duration of time (in seconds)
    :param payload: dictionary containing JSON content
    :param kwargs: extra JSON data to send, omitting ACCESS_CODE (which is automatically included)
    :return: decoded JSON response as dict or list.
    """
    if method not in ('GET', 'DELETE', ):
        # automatically insert settings.py access_code
        payload['access_code'] = settings.ACCESS_CODE
        payload.update(kwargs)
    else:
        payload = {}

    try:
        with async_timeout.timeout(timeout):
            async with session.request(method, url, data=json.dumps(payload),
                                       headers={'content-type': 'application/json'}) as resp:

                # if an HTTP error code is returned, stop heating
                if resp.status >= 400:
                    if settings.DEBUG:
                        print(await resp.text())
                    raise StopHeatingError

                res = await resp.json()
                if settings.DEBUG:
                    print('{0} {1}'.format(method, url))
                return res

    # if server connection times out, stop heating
    except asyncio.TimeoutError:
        raise StopHeatingError


class NetworkQueue(asyncio.Queue):
    """A Queue object with additional attribute to store last time an item was retrieved and processed."""
    def __init__(self, *args, **kwargs):
        self.last_time = time.time()
        self.threshold_time = kwargs.pop('threshold_time') or settings.WEB_API_ACTIVE_INTERVAL
        self.threshold_qsize = kwargs.pop('threshold_qsize') or settings.WEB_API_MIN_UPLOAD_LENGTH
        super(NetworkQueue, self).__init__(*args, **kwargs)


async def batch_upload(loop, network_queue, run_id):
    """An asynchronous function that uploads payloads by consuming from the network queue
    only when a specified amount of time has passed from time of last processing
    and when a specified number of items exist in the queue.
    The asynchronous process breaks otherwise.

    :param loop: the main event loop
    :param network_queue: a Network Queue object.
    :param run_id: the unique ID for a calorimetry job from the web API

    :exception StopHeatingError: When this error is raised, any async function that calls it
    must give control back to the idle loop and stop heating.
    Raised if a 'stop_flag' field returns True from the web API response.

    :exception SampleNotInsertedError: Indicates that the user has not put the sample in the cell,
    the heating functions should hold the set point at instructed start temp for a calorimetry job
    when this error occurs.
    """

    while True:
        # Only make HTTP requests above certain item number threshold
        # and after a set amount of time since last upload
        if network_queue.qsize() >= network_queue.threshold_qsize \
                and (time.time() - network_queue.last_time) >= network_queue.threshold_time:

            # collect all items in the queue
            data = await asyncio.gather(
                *[asyncio.ensure_future(network_queue.get()) for _ in range(network_queue.qsize())],
                loop=loop
            )

            # make the request and clear the local waiting list
            async with aiohttp.ClientSession(loop=loop) as session:
                response = await fetch(session, 'POST', settings.WEB_API_DATA_ADDRESS,
                                       payload={'data': data, 'run': run_id})
            if settings.DEBUG:
                print(response)

            # reset network queue last processed time
            network_queue.last_time = time.time()

            # Check for stop heating and sample inserted flags from the web API
            if response.get('stop_flag'):
                raise StopHeatingError
            return response.get('is_ready')
        else:
            break


def clamp(number, min_number=0, max_number=100):
    """
    A function that clamps the input argument number within the given range.
    :param number: The number to be clamped.
    :param min_number: Minimum value the clamped result can take.
    :param max_number: Maximum value the clamped result can take.
    :return: The clamped result.
    """
    res = number
    if number > max_number:
        res = max_number
    elif number < min_number:
        res = min_number
    return res


def roughly_equal(*args, tolerence=1e-02):
    """
    Compares argument inputs for equality.
    If all of their differences with each other are within the set tolerance, return True, vice versa.
    :param args: Compared numbers.
    :param tolerence: If all differences between inputs are within this value, return True.
    :return: Whether the arguments are roughly equal to each other.
    """
    for _prev, _next in combinations(args, r=2):
        if abs(_prev - _next) <= tolerence:
            return False
    return True
