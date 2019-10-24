import glob
import time
import os
from multiprocessing import Process

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import sys
del sys.modules['layman']

from layman.layer.filesystem import input_chunk
from layman.layer import LAYER_TYPE
from layman import app, settings
from layman.uuid import check_redis_consistency


PORT = 8000

num_layers_before_test = 0

@pytest.fixture(scope="module")
def client():

    # print('before app.test_client()')
    client = app.test_client()

    # print('before Process(target=app.run, kwargs={...')
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': PORT,
        'debug': False,
    })
    # print('before server.start()')
    server.start()
    time.sleep(1)

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = f'{settings.LAYMAN_DOCKER_MAIN_SERVICE}:{PORT}'
    app.config['SESSION_COOKIE_DOMAIN'] = f'{settings.LAYMAN_DOCKER_MAIN_SERVICE}:{PORT}'

    # print('before app.app_context()')
    with app.app_context() as ctx:
        publs_by_type = check_redis_consistency()
        global num_layers_before_test
        num_layers_before_test = len(publs_by_type[LAYER_TYPE])
        yield client

    # print('before server.terminate()')
    server.terminate()
    # print('before server.join()')
    server.join()


@pytest.fixture(scope="module")
def chrome():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    desired_capabilities = DesiredCapabilities.CHROME
    desired_capabilities['loggingPrefs'] = {'browser': 'ALL'}
    chrome = webdriver.Chrome(
        options=chrome_options,
        desired_capabilities=desired_capabilities,
    )
    chrome.set_window_size(1000,2000)
    yield chrome
    chrome.close()
    chrome.quit()


def test_post_layers_chunk(client, chrome):
    check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test
    })

    username = 'testuser1'
    layername = 'country_chunks'
    file_paths = list(map(lambda fp: os.path.join(os.getcwd(), fp), [
        'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]))
    for fp in file_paths:
        assert os.path.isfile(fp)

    domain = f"http://localhost:{PORT}"
    client_url = f'http://{settings.LAYMAN_CLIENT_DOCKER_SERVICE}:3000/client/'

    r = requests.get(client_url)
    assert r.status_code==200

    chrome.get(client_url)
    chrome.set_window_size(1000,2000)
    # chrome.save_screenshot('/code/tmp/test-1.png')

    user_input = chrome.find_elements_by_name('user')
    assert len(user_input) == 1
    user_input = user_input[0]
    user_input.clear()
    user_input.send_keys(username)

    layername_input = chrome.find_elements_by_name('name')
    assert len(layername_input) == 1
    layername_input = layername_input[0]
    layername_input.clear()
    layername_input.send_keys(layername)

    file_input = chrome.find_elements_by_name('file')
    assert len(file_input) == 1
    file_input = file_input[0]
    # print(" \n ".join(file_paths))
    file_input.send_keys(" \n ".join(file_paths))
    # chrome.save_screenshot('/code/tmp/test-2.png')

    button = chrome.find_elements_by_xpath('//button[@type="submit"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    time.sleep(0.1)

    layer_url = f'{domain}/rest/{username}/layers/{layername}?'
    r = requests.get(layer_url)
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file']
    max_attempts = 20
    attempts = 1
    while not (r.status_code == 200 and all(
        'status' not in r.json()[k] for k in keys_to_check
    )):
        # print('waiting')
        time.sleep(0.5)
        r = requests.get(layer_url)
        attempts += 1
        if attempts > max_attempts:
            # chrome.save_screenshot('/code/tmp/test-2.5.png')
            raise Exception('Max attempts reached!')
    # chrome.save_screenshot('/code/tmp/test-3.png')

    entries = chrome.get_log('browser')
    assert len(entries) > 3
    for entry in entries:
        # print(entry)
        assert entry['level'] == 'INFO' or (
            entry['level'] == 'SEVERE'
            and entry['message'].startswith(
                f'{client_url}rest/{username}/layers/{layername}/chunk?'
            ) and entry['message'].endswith('Failed to load resource: the server responded with a status of 404 (NOT FOUND)')
        )
    total_chunks_key = input_chunk.get_layer_redis_total_chunks_key(username, layername)
    assert not settings.LAYMAN_REDIS.exists(total_chunks_key)

    check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 1
    })


def test_patch_layer_chunk(client, chrome):
    username = 'testuser1'
    layername = 'country_chunks'

    pattern = os.path.join(os.getcwd(), 'tmp/naturalearth/110m/cultural/*')
    file_paths = glob.glob(pattern)

    # file_paths = list(map(lambda fp: os.path.join(os.getcwd(), fp), [
    #     'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
    # ]))
    for fp in file_paths:
        # print('fp', fp)
        assert os.path.isfile(fp)

    domain = f"http://localhost:{PORT}"
    client_url = f'http://{settings.LAYMAN_CLIENT_DOCKER_SERVICE}:3000/client/'


    r = requests.get(client_url)
    assert r.status_code==200

    chrome.get(client_url)
    # chrome.save_screenshot('/code/tmp/test-1.png')

    button = chrome.find_elements_by_xpath('//button[text()="PATCH"]')
    assert len(button) == 1
    button = button[0]
    button.click()
    # chrome.save_screenshot('/code/tmp/test-2.png')

    user_input = chrome.find_elements_by_name('user')
    assert len(user_input) == 1
    user_input = user_input[0]
    user_input.clear()
    user_input.send_keys(username)

    layername_input = chrome.find_elements_by_name('name')
    assert len(layername_input) == 1
    layername_input = layername_input[0]
    layername_input.clear()
    layername_input.send_keys(layername)

    file_input = chrome.find_elements_by_name('file')
    assert len(file_input) == 1
    file_input = file_input[0]
    # print(" \n ".join(file_paths))
    file_input.send_keys(" \n ".join(file_paths))
    # chrome.save_screenshot('/code/tmp/test-3.png')

    button = chrome.find_elements_by_xpath('//button[@type="submit"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    time.sleep(0.1)

    layer_url = f'{domain}/rest/{username}/layers/{layername}?'
    r = requests.get(layer_url)
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file']
    max_attempts = 20
    attempts = 1
    while not (r.status_code == 200 and all(
        'status' not in r.json()[k] for k in keys_to_check
    )):
        # print('waiting')
        time.sleep(0.5)
        r = requests.get(layer_url)
        attempts += 1
        if attempts > max_attempts:
            # chrome.save_screenshot('/code/tmp/test-4.png')
            raise Exception('Max attempts reached!')
    # chrome.save_screenshot('/code/tmp/test-4.png')

    entries = chrome.get_log('browser')
    assert len(entries) > 3
    for entry in entries:
        # print(entry)
        assert entry['level'] == 'INFO' or (
            entry['level'] == 'SEVERE'
            and entry['message'].startswith(
                f'{client_url}rest/{username}/layers/{layername}/chunk?'
            ) and entry['message'].endswith('Failed to load resource: the server responded with a status of 404 (NOT FOUND)')
        )
    total_chunks_key = input_chunk.get_layer_redis_total_chunks_key(username, layername)
    assert not settings.LAYMAN_REDIS.exists(total_chunks_key)

    check_redis_consistency(expected_publ_num_by_type={
        f'{LAYER_TYPE}': num_layers_before_test + 1
    })

