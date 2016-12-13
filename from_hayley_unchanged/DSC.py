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
rate = 0.1          # degrees per second
kp = 1.8        # proportional
ki = 1          # integral
kd = 0.         # differential
start_temp = 30     
final_temp = 100

'''
Setup
'''
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)    # heater_sample
GPIO.setup(13, GPIO.OUT)    # heater_ref
GPIO.setup(16, GPIO.OUT)    # LED red
GPIO.setup(21, GPIO.OUT)    # LED blue
GPIO.setup(20, GPIO.OUT)    # LED green
GPIO.output(16, GPIO.LOW)    # LED red
GPIO.output(21, GPIO.LOW)    # LED blue
GPIO.output(20, GPIO.LOW)    # LED green

GPIO.output(20, GPIO.HIGH)       # Turn on LED green (standby)
time.sleep(5)

heater_ref = GPIO.PWM(13, 1)  # pin, freq
heater_sample = GPIO.PWM(12, 1)  # pin, freq

# Initialize the GPIO Pins
os.system('modprobe w1-gpio')  # Turns on the GPIO module
os.system('modprobe w1-therm')  # Turns on the Temperature module

# Finds the correct device file that holds the temperature data
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '3b-6*')[0]  ### whats the point of this if device_folder is overwritten in the read_Temp function?
device_file = device_folder + '/w1_slave'  ### ^
ref_no = '3b-6*'  ### would be slightly quicker if exact paths are used instead of wildcards
sample_no = '3b-0*'  ### ^


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
    ### this is not true, lines will stil contain the same thing because it was not updated,
    ### to read it again, file must be opened with open(device_file, 'r') again
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()  ### where is this function?

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

        ### this 'while True' loop will not be broken (and calorimtery cannot formally begin)
        ### unless we KeyboardInterrupt
        ### which is not feasible if we want this to be remotely controlled

            while abs(read_temp(ref_no) - start_temp) > 1 and abs(read_temp(ref_no) - start_temp) > 1:
                
                GPIO.output(20,GPIO.LOW)      # LED green (standby) off
                GPIO.output(21,GPIO.HIGH)     # LED blue (getting to start temp) on

                temp_ref = read_temp(ref_no)
                temp_sample = read_temp(sample_no)
                set_point = start_temp      
                
                # reference
                ### where is this p_ref obejct created?
                p_ref.setPoint(set_point) # updates the setpoint
                duty_cycle_ref = p_ref.update(temp_ref)
                if (duty_cycle_ref<0):
                    duty_cycle_ref=0
                elif (duty_cycle_ref>100): # maximum power 3.5V (70% of 5V)
                    duty_cycle_ref=100
                
                # sample
                p_sample.setPoint(set_point) # updates the setpoint
                duty_cycle_sample = (p_sample.update(temp_sample))

                ### we can extract this number camlping logic to a separate reusable function
                if (duty_cycle_sample<0):
                    duty_cycle_sample=0
                elif (duty_cycle_sample>100): # maximum power 3.5V (70% of 5V)
                    duty_cycle_sample=100

                heater_ref.ChangeDutyCycle(duty_cycle_ref)
                heater_sample.ChangeDutyCycle(duty_cycle_sample)
                time.sleep(0.5) 
            time.sleep(5)   # sleep for 5 seconds to settle down on start temperature

    #STOP if pres ctrl c
    except KeyboardInterrupt:
        heater_ref.stop()
        heater_sample.stop()
        GPIO.output(16,GPIO.LOW)     # LED red (heating) off
        GPIO.output(20,GPIO.HIGH)    # LED green (standby) off
        GPIO.output(21,GPIO.LOW)     # LED blue (getting to start temp) off
        GPIO.cleanup()


def run_calorimetry():
    
    '''
    Runs a full DCS cycle
    '''

    GPIO.output(20, GPIO.LOW)        # LED green (standby) off
    GPIO.output(21, GPIO.LOW)        # LED blue (getting to start temp) off
    GPIO.output(16, GPIO.HIGH)           # LED red (heating) on

    t0 = time.time()            # start timer
    pause_time = 1/(10*rate)        # seconds delay to chose rate
    temp_steps = np.linspace(30, 100, 701)  # steps of 0.1 degrees
    ### the 0.1 increment is hardwired
    set_point = start_temp          # initially set set point to starting temp
    
    #start PID
    p_ref = pid.PID(kp, ki, kd, Integrator_max=100, Integrator_min=0)
    p_sample = pid.PID(kp, ki, kd, Integrator_max=100, Integrator_min=0)
    p_ref.setPoint(set_point)       
    p_sample.setPoint(set_point)   

    #start PWM with duty cycle = 0
    heater_ref.start(0)     
    duty_cycle_ref=0
    heater_sample.start(0)  
    duty_cycle_sample=0

    try:
        while True:

            ### this while True with KeyboardInterrupt pattern needs refactoring

            for i in temp_steps:

                ### at the end of temp_steps, although we have set the setPoint to the target temp,
                ### we still need to be continuously updating the PWM
                ### there could be errors that needs to be accounted for by the PID algorithm even after the final setPoint change
                ### but the PID calculations end straight away as is.
                ### PID calculations needs to be continuously running until device reaches final temp

                temp_ref = read_temp(ref_no)
                temp_sample = read_temp(sample_no)
                set_point = start_temp
                if i -2 < temp_ref < i + 2 and i - 2 < temp_sample < i + 2:    # check if old temp is within error
                    set_point = i +0.1     # increase setpoint by 1

                
                # reference PID
                p_ref.setPoint(set_point) # updates the setpoint
                duty_cycle_ref = (p_ref.update(temp_ref))
                if (duty_cycle_ref<0):
                    duty_cycle_ref=0
                if (duty_cycle_ref>100): 
                    duty_cycle_ref=100
                
                # sample PID
                p_sample.setPoint(set_point) # updates the setpoint
                duty_cycle_sample = (p_sample.update(temp_sample))
                if (duty_cycle_sample<0):
                    duty_cycle_sample=0
                if (duty_cycle_sample>100): 
                    duty_cycle_sample=100
                #update PWM duty cycle
                heater_ref.ChangeDutyCycle(duty_cycle_ref)
                heater_sample.ChangeDutyCycle(duty_cycle_sample)

                # get current here

                # calculate power
                ### we can extract these patterns into a separate function
                voltage_ref = mav_voltage * duty_cycle_ref / 100
                voltage_sample = mav_voltage * duty_cycle_sample / 100
                power_ref = voltage_ref * current_ref
                power_sample = voltage_sample * current_sample
                power_DCS = abs(power_sample - power_ref)
                
                time_elapsed = time.time()-t0
                data = pd.DataFrame([[time_elapsed, set_point, read_temp(ref_no),read_temp(sample_no),voltage_ref,voltage_sample]],columns = ('Time', 'Setpoint', 'Ref Temp', 'Sample Temp', 'Ref Voltage', 'Sample Voltage'))
                print (data)
                sleep(pause_time)

    #STOP if pres ctrl c
    except KeyboardInterrupt:
        heater_ref.stop()
        heater_sample.stop()
        GPIO.output(16,GPIO.LOW)     # LED red (heating) off
        GPIO.output(20,GPIO.HIGH)    # LED green (standby) off
        GPIO.output(21,GPIO.LOW)     # LED blue (getting to start temp) off
        GPIO.cleanup()

def start():
    ### both are ref temps below
    if abs(read_temp(ref_no) - start_temp) <= 1 and abs(read_temp(ref_no) - start_temp) <= 1:
        run_calorimetry()
    else:
        get_ready_to_start()
        run_calorimetry()

start()

