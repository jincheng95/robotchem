"""
Change the variables in this file to specify:
1. component pin numbers on GPIO board,
2. default PID parameters,
3. website URL or IP address to which data is sent,
4. time intervals to measure and send data

Jin Cheng, 12/12/16
"""

# Set this to True in code development,
# False in testing and presentation
DEBUG = True

# PID controller settings
PID_PARAMS = {
    'P': 50.,
    'I': 6.9,
    'D': 0.003,
}


# Web API Address
WEB_API_BASE_ADDRESS = "http://robotchem.chengj.in/api/"
WEB_API_STATUS_ADDRESS = WEB_API_BASE_ADDRESS + "status/"
WEB_API_DATA_ADDRESS = WEB_API_BASE_ADDRESS + "data/"

# Web API Connection Interval, in seconds
WEB_API_IDLE_INTERVAL = 10
WEB_API_ACTIVE_INTERVAL = 5

# Web API comms access code
ACCESS_CODE = "tuckfrump"


# Main loop interval, in seconds
# This is the increment between calculations of PID-controlled PWM when a job is active
MAIN_LOOP_INTERVAL = 0.5

# Temperature sensor IDs
TEMP_SENSOR_BASE_DIR = "/sys/bus/w1/devices/"
TEMP_SENSOR_ID_REF = "3b-6cdc038848fb"
TEMP_SENSOR_ID_SAMPLE = "3b-0cdc0388554f"
TEMP_SENSOR_ID_APPENDIX = "/w1_slave"

# Temperature read time interval
# This is used during an active calorimetry job, during the main PID calculating loop
TEMP_READ_TIME_INTERVAL = 0.2

# The difference between temperature values for them to be considered 'practically equal'
TEMP_TOLERANCE = 1


# Various PINS
# All pin numbers are for the BCM Board numbering system
# LHS = left hand side (Sample)
# RHS = right hand side (Reference)

CURRENT_SENSOR_REF = 14  # LHS
CURRENT_SENSOR_SAMPLE = 3  # RHS

HEATER_REF = 12  # PWM, MOSFET, LHS
HEATER_SAMPLE = 13  # PWM, MOSFET, RHS

RED = 16
BLUE = 21
GREEN = 20