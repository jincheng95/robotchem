"""
Change the variables in this file to specify:

#. component pin numbers on GPIO board,
#. default PID parameters,
#. website URL or IP address to which data is sent,
#. time intervals to measure and send data

Some parameters can be controlled by the website's Calibrate page,
and the corresponding params listed here are defaults in case web connection fails.

Jin Cheng, 12/12/16:
    Moved all hardware settings that are sensitive to circuitry changes to this separate file for easy & quick changes.

Jin Cheng, 17/01/16:
    Added Web API settings.
"""


#
# ==========================================
# General
# ==========================================
#
DEBUG = True
"""Setting this to true enables a very basic logging system which just prints out to `stdout` various info
about what the code is doing."""

FAKE_HARDWARE = True
"""Sometimes it is useful to run `main.py` on a personal computer and disable hardware controls. Setting this to true
will make hardware control functions just print out what it was supposed to do."""


PID_PARAMS = {
    'P': 3.,
    'I': 0.6,
    'D': 0.,
}
"""Default PID controller parameter dictionary. Keys should be `P`, `I`, `D` which correspond to the proportional,
integral and derivative factors. Note the web API PID parameters override this setting."""


MAX_RAMP_RATE = 0.5
"""Maximum increment in temperature (degrees Celsius) each cycle.
Note the web API parameters override this setting."""


#
# ==========================================
# Web API Settings
# ==========================================
#
# WEB_API_BASE_ADDRESS = "http://127.0.0.1:8000/api/"
WEB_API_BASE_ADDRESS = "http://robotchem.chengj.in/api/"
"""Web API base address."""

WEB_API_STATUS_ADDRESS = WEB_API_BASE_ADDRESS + "status/"
WEB_API_DATA_ADDRESS = WEB_API_BASE_ADDRESS + "data/"

# Web API Connection Interval, in seconds
WEB_API_IDLE_INTERVAL = 10
"""Idle refresh interval. Note the web API parameters override this setting."""

WEB_API_ACTIVE_INTERVAL = 5
"""Active job refresh interval. Note the web API parameters override this setting."""

WEB_API_MIN_UPLOAD_LENGTH = 5
"""Minimum number of measurements that justifies sending a HTTP request.
Note the web API parameters override this setting."""

# Web API comms access code
# Change this in local_settings.py in production
# settings.py is publicly viewable through GitHub but local_settings.py is ignored by Git
try:
    from robotchem.local_settings import ACCESS_CODE
except ImportError:
    ACCESS_CODE = "SUPER_SECRET_PASSWORD"

#
# ==========================================
# LOOP TIME INTERVAL SETTINGS
# ==========================================

MAIN_LOOP_INTERVAL = 0.5
"""
Main loop interval, in seconds. This is the increment between calculations of PID-controlled PWM when a job is active.
Note the web API parameters override this setting.
"""

#
# ==========================================
# Temperature Sensor Settings
# ==========================================

TEMP_SENSOR_BASE_DIR = "/sys/bus/w1/devices/"
"""Base directory of the 1-wire raspberry pi reader files."""

TEMP_SENSOR_ID_SAMPLE = "3b-6cdc038848fb"
"""Identifier of the 1-wire reader port connected to the sample thermocouple."""

TEMP_SENSOR_ID_REF = "3b-0cdc0388554f"
"""Identifier of the 1-wire reader port connected to the reference thermocouple."""

TEMP_SENSOR_ID_APPENDIX = "w1_slave"
"""Appendix to the file names for the 1-wire data files on the file system on Raspberry Pi."""


TEMP_READ_TIME_INTERVAL = 0.2
""" Temperature read time interval
This is used during an active calorimetry job, during the main PID calculating loop
"""

TEMP_TOLERANCE = 1
"""The difference between temperature values for them to be considered 'practically equal'"""

TEMP_STABILISATION_MIN_DURATION = 15
"""The minimum time duration in which temperature must stabilise before the program moves on to the next code block."""


#
# ==========================================
# Current Sensor Settings
# ==========================================
MAX_VOLTAGE = 3.3
"""Voltage supplied across the MOSFETs which power the Peltier heaters. Used to calculate energy used."""


#
# ==========================================
# Pin Numbers on Raspberry Pi GPIO Board
# ==========================================
#
"""
USE THE BCM BOARD NUMBERING SYSTEM!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""

CURRENT_SENSOR_REF_CHANNEL = 1  # ADC channel number
"""Analog-digital converter channel used for the current sensor on the reference heater."""

CURRENT_SENSOR_SAMPLE_CHANNEL = 3  # ADC channel number
"""Analog-digital converter channel used for the current sensor on the sample heater."""

HEATER_REF_PIN = 12  # PWM, MOSFET, LHS
"""Reference heater MOSFET PWM pin. Note this must be a hardware controlled GPIO pin."""

HEATER_SAMPLE_PIN = 13  # PWM, MOSFET, RHS
"""Reference heater MOSFET PWM pin. Note this must be a hardware controlled GPIO pin."""

RED = 16
"""Red LED GPIO output pin number."""

BLUE = 21
"""Blue LED GPIO output pin number."""

GREEN = 20
"""Green LED GPIO output pin number."""
