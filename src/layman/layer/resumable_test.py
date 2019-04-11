import glob
import time
import os
from multiprocessing import Process

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from layman.layer.filesystem import input_chunk
from layman.layer import LAYER_TYPE
from layman import app, settings
from layman.uuid import check_redis_consistency

PORT = 9002


@pytest.fixture(scope="module")
def flask_server():
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': PORT,
        'debug': False,
    })
    # print('START FLASK SERVER')
    server.start()
    yield server
    # print('STOP FLASK SERVER')
    server.terminate()
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
    # print('STOP FLASK SERVER')
    chrome.close()
    chrome.quit()


@pytest.mark.usefixtures("flask_server")
def test_post_layers_chunk(chrome):
    username = 'testuser1'
    layername = 'country_chunks'
    file_paths = list(map(lambda fp: os.path.join(os.getcwd(), fp), [
        'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]))
    for fp in file_paths:
        assert os.path.isfile(fp)

    domain = f"http://localhost:{PORT}"

    r = requests.get(domain+'/static/test-client/index.html')
    assert r.status_code==200

    chrome.get(domain+'/static/test-client/index'
                      '.html')
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
            raise Exception('Max attempts reached!')
    # chrome.save_screenshot('/code/tmp/test-3.png')

    entries = chrome.get_log('browser')
    assert len(entries) > 3
    for entry in entries:
        # print(entry)
        assert entry['level'] == 'INFO' or (
            entry['level'] == 'SEVERE'
            and entry['message'].startswith(
                f'{domain}/rest/{username}/layers/{layername}/chunk?'
            ) and entry['message'].endswith('Failed to load resource: the server responded with a status of 404 (NOT FOUND)')
        )
    total_chunks_key = input_chunk.get_layer_redis_total_chunks_key(username, layername)
    assert not settings.LAYMAN_REDIS.exists(total_chunks_key)

    with app.app_context():
        check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': 3
        })


@pytest.mark.usefixtures("flask_server")
def test_patch_layer_chunk(chrome):
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


    r = requests.get(domain+'/static/test-client/index.html')
    assert r.status_code==200

    chrome.get(domain+'/static/test-client/index'
                      '.html')
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
                f'{domain}/rest/{username}/layers/{layername}/chunk?'
            ) and entry['message'].endswith('Failed to load resource: the server responded with a status of 404 (NOT FOUND)')
        )
    total_chunks_key = input_chunk.get_layer_redis_total_chunks_key(username, layername)
    assert not settings.LAYMAN_REDIS.exists(total_chunks_key)

    with app.app_context():
        check_redis_consistency(expected_publ_num_by_type={
            f'{LAYER_TYPE}': 3
        })

