"""
Change the variables in this file to specify:
1. component pin numbers on GPIO board,
2. default PID parameters,
3. website URL or IP address to which data is sent.
"""

PINS = {
    'temp_sensor_sample': 1,
    'temp_sensor_ref': 2,

    'heater_sample': 3,
    'heater_ref': 4,

    'power_LED': 5,
    'heating_init_LED': 6,    # the red LED
    'heating_sample_LED': 7,  # the amber LED
    'cooling_sample_LED': 8   # the green LED
}

TEMP_SENSOR_ID_SAMPLE = ""
TEMP_SENSOR_ID_REF = ""

PID_PARAMS = {
    'P': 50.,
    'I': 6.9,
    'D': 0.003,
}

WEB_API_ADDRESS = "http://chengj.in/robotchem/api/"
