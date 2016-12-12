import RPi.GPIO as GPIO
import pid as pid
import time
from time import sleep
import os
import glob
import numpy as np
import pandas as pd

'''
Settings
'''
rate = 0.1              # degrees per second
kp = 1.8                # proportional
ki = 1                  # integral
kd = 0.                 # differential
start_temp = 30         
final_temp = 100

'''
Setup
'''
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)        # heater_sample
GPIO.setup(13, GPIO.OUT)        # heater_ref
GPIO.setup(16, GPIO.OUT)        # LED red
GPIO.setup(21, GPIO.OUT)        # LED blue
GPIO.setup(20, GPIO.OUT)        # LED green
GPIO.output(16,GPIO.LOW)        # LED red
GPIO.output(21,GPIO.LOW)        # LED blue
GPIO.output(20,GPIO.LOW)        # LED green

GPIO.output(20,GPIO.HIGH)       # Turn on LED green (standby)
time.sleep(5)

heater_ref = GPIO.PWM(13,1)  # pin, freq
heater_sample = GPIO.PWM(12,1)  # pin, freq

# Initialize the GPIO Pins
os.system('modprobe w1-gpio')  # Turns on the GPIO module
os.system('modprobe w1-therm') # Turns on the Temperature module

# Finds the correct device file that holds the temperature data
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '3b-6*')[0]
device_file = device_folder + '/w1_slave'
ref_no = '3b-6*'
sample_no = '3b-0*'


def read_temp(number):
        
        '''
        Reads temperature from sensors
        '''
        
        # Reads temperature data
        device_folder = glob.glob(base_dir + number)[0]
        device_file = device_folder + '/w1_slave'
        f = open(device_file, 'r')                      
        lines = f.readlines()                           
        f.close()

        # While the first line does not contain 'YES', wait for 0.2s and then read the device file again.
        while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = read_temp_raw()

        # Look for the position of the '=' in the second line of the device file.
        equals_pos = lines[1].find('t=')

        # If the '=' is found, convert the rest of the line after the '=' into degrees Celsius, then degrees Fahrenheit
        if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 1000.0
                return temp_c


def get_ready_to_start():

        '''
        Get hotplates to starting temperature
        '''

        try:
                while True:
                                
                                GPIO.output(20,GPIO.LOW)          # LED green (standby) off
                                GPIO.output(21,GPIO.HIGH)         # LED blue (getting to start temp) on

                                temp_ref = read_temp(ref_no)
                                temp_sample = read_temp(sample_no)
                                set_point = start_temp          
                                
                                # reference
                                p_ref.setPoint(set_point) # updates the setpoint
                                duty_cycle_ref = (p_ref.update(temp_ref))
                                if (duty_cycle_ref<0):
                                        duty_cycle_ref=0
                                if (duty_cycle_ref>100): # maximum power 3.5V (70% of 5V)
                                        duty_cycle_ref=100
                                
                                # sample
                                p_sample.setPoint(set_point) # updates the setpoint
                                duty_cycle_sample = (p_sample.update(temp_sample))
                                if (duty_cycle_sample<0):
                                        duty_cycle_sample=0
                                if (duty_cycle_sample>100): # maximum power 3.5V (70% of 5V)
                                        duty_cycle_sample=100

                                heater_ref.ChangeDutyCycle(duty_cycle_ref)
                                heater_sample.ChangeDutyCycle(duty_cycle_sample)
                                time.sleep(0.5) 
                        time.sleep(5)   # sleep for 5 seconds to settle down on start temperature

        #STOP if pres ctrl c
        except KeyboardInterrupt:
                heater_ref.stop()
                heater_sample.stop()
                GPIO.output(16,GPIO.LOW)         # LED red (heating) off
                GPIO.output(20,GPIO.HIGH)        # LED green (standby) off
                GPIO.output(21,GPIO.LOW)         # LED blue (getting to start temp) off
                GPIO.cleanup()


get_ready_to_start()

