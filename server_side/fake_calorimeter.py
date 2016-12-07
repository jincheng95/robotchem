import requests
import datetime
import time
import random
import math

# URL = "http://127.0.0.1:8000/api/data/"
URL = "http://robotchem.chengj.in/api/data/"

RUN_ID = 3

START = 7
STOP = 100
POWER = 0.5


def pair_of_random_data(mu=random.random() * 100, sigma=random.random() * 0.8):
    return random.gauss(mu, sigma), random.gauss(mu, sigma)


if __name__ == '__main__':
    while START < STOP:
        payload = []
        for i in range(6):
            temps = pair_of_random_data(START)
            heat = math.cos(temps[0]), math.cos(temps[0] + 3.1415)
            data_point = {
                'measured_at': datetime.datetime.now().isoformat(),
                'temp_ref': temps[0],
                'temp_sample': temps[1],
                'heat_ref': heat[0],
                'heat_sample': heat[1],
                'run': RUN_ID,
                'access_code': 'tuckfrump',
            }
            START += random.random() * POWER
            payload.append(data_point)
            time.sleep(0.88)

        r = requests.post(URL, json=payload)
        print(r)
        time.sleep(1)
