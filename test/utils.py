import requests
import time
from requests.exceptions import ConnectionError


# utils
def wait_for_url(url, max_attempts, sleeping_time):
    attempt = 1
    while True:
        # print(f"Waiting for URL {url}, attempt {attempt}")
        try:
            r = requests.get(url)
            break
        except ConnectionError as e:
            if attempt == max_attempts:
                print(f"Max attempts reached")
                raise e
            attempt += 1
        time.sleep(sleeping_time)
