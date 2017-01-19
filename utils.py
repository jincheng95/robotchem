"""
Utility functions and classes for common calculations and networking patterns.

Jin Cheng 12/12/16:
    StopHeatingError, async :func:`fetch` function that makes HTTP requests.
    The Network queue.
    Number manipulation functions.
"""

import asyncio
import json
import time
from itertools import combinations

import async_timeout

from robotchem import settings


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

    def put(self, *args, **kwargs):
        if settings.DEBUG:
            print("Network queue size: {0}".format(self.qsize() + 1))
        return super(NetworkQueue, self).put(*args, **kwargs)


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
        if abs(_prev - _next) >= float(tolerence):
            return False
    return True
