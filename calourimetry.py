"""
Main logic and multiprocessing for performing a calorimetry.
"""

import numpy as np
import pandas as pd
import time
from .hardware import read_from_ref, read_from_sample, read_from_average, PID


def _roughly_equal(float1, float2, tolerance=1e-2):
    return abs(float1 - float2) <= tolerance


class Run(object):
    """
    Represents a single Differential Scanning Calorimetry experiment.
    Contains all logic required to perform such process and spawns additional parallel processes as needed.
    """

    def __init__(self, start, end, time_increment=0.1):
        self.start, self.end, self.time_increment = float(start), float(end), float(time_increment)
        self.PID_ref, self.PID_sample = None, None

        self.readings = pd.DataFrame()

        self.last_temp_reading = 0.
        self.last_power_out = 0.

    def is_ready(self, **kwargs):
        """
        Performs a check to see if current averaged temperature in the chamber
        :param kwargs: tolerance in temperature difference.
        :return: Boolean, whether current averaged temperature is approx. the specified start temperature.
        """
        equal_temp = lambda temp: _roughly_equal(self.start, temp, **kwargs)
        return equal_temp(read_from_sample()) and equal_temp(read_from_average())

    def start(self):
        if self.is_ready():
            self.ramp()
        # else:
            # self.heat_or_cool_to_start_temp()

    def ramp(self):
        """
        Starts temperature ramp.
        """
        pass
