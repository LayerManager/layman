import requests
import time
from requests.exceptions import ConnectionError


# utils
def wait_for_url(url, max_attempts, sleeping_time):
    attempt = 1
    while True:
        # print(f"Waiting for URL {url}, attempt {attempt}")
        try:
            # Just checking the url, no need to store result
            requests.get(url)
            break
        except ConnectionError as e:
            if attempt == max_attempts:
                print(f"Max attempts reached")
                raise e
            attempt += 1
        time.sleep(sleeping_time)


def assert_same_infos(info_to_test,
                      expected_info,
                      more_info=None):
    for publication_name in info_to_test:
        if info_to_test[publication_name].get('id'):
            del info_to_test[publication_name]['id']
    assert info_to_test == expected_info, (info_to_test, expected_info, more_info)
