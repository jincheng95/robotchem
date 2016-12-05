import requests
import datetime
import time
import random

URL = "http://ch-nettle.ch.ic.ac.uk:8181/api/data/"


def pair_of_random_data():
    mu = random.random() * 100
    sigma = random.random()
    return random.gauss(mu, sigma), random.gauss(mu, sigma)


if __name__ == '__main__':
    while True:
        payload = []
        for i in range(6):
            temps = pair_of_random_data()
            heat = pair_of_random_data()
            data_point = {
                'measured_at': datetime.datetime.now().isoformat(),
                'temp_ref': temps[0],
                'temp_sample': temps[1],
                'heat_ref': heat[0],
                'heat_sample': heat[1],
                'run': 1,
                'access_code': 123456
            }
            payload.append(data_point)
            time.sleep(0.88)

        r = requests.post(URL, json=payload)
        print(r)
        time.sleep(0.1)
