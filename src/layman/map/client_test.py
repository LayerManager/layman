import json
import time
from multiprocessing import Process

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

import sys
del sys.modules['layman']

from layman.map import MAP_TYPE
from layman import app, settings
from layman.uuid import check_redis_consistency


PORT = 8000

num_maps_before_test = 0

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
        global num_maps_before_test
        num_maps_before_test = len(publs_by_type[MAP_TYPE])
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


def test_post_no_file(client, chrome):
    check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': num_maps_before_test
    })

    username = 'testuser2'
    client_url = f'http://{settings.LAYMAN_CLIENT_DOCKER_SERVICE}:3000/client/'

    r = requests.get(client_url)
    assert r.status_code==200

    chrome.get(client_url)
    chrome.set_window_size(1000,2000)
    # chrome.save_screenshot('/code/tmp/test-1.png')

    map_tab = chrome.find_elements_by_css_selector('.ui.attached.tabular.menu > a.item:nth-child(2)')
    assert len(map_tab) == 1
    map_tab = map_tab[0]
    map_tab.click()

    user_input = chrome.find_elements_by_name('user')
    assert len(user_input) == 1
    user_input = user_input[0]
    user_input.clear()
    user_input.send_keys(username)

    button = chrome.find_elements_by_xpath('//button[@type="submit"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    time.sleep(0.1)

    # chrome.save_screenshot('/code/tmp/test-3.png')

    resp_msg_div = chrome.find_elements_by_css_selector('div.ui.container > div:nth-child(8) > div.ui.segment > div.ui.negative.message > code')
    assert len(resp_msg_div) == 1
    resp_msg_div = resp_msg_div[0]
    resp_json = json.loads(resp_msg_div.text)
    assert resp_json['code'] == 1

    entries = chrome.get_log('browser')
    assert len(entries) == 1

    severe_entries = [e for e in entries if e['level'] == 'SEVERE']
    assert len(severe_entries) == 1
    for entry in severe_entries:
        assert entry['message'].startswith(f'{client_url}rest/{username}/maps?'
            ) and entry['message'].endswith(
            'Failed to load resource: the server responded with a status of 400 (BAD REQUEST)')

    check_redis_consistency(expected_publ_num_by_type={
        f'{MAP_TYPE}': num_maps_before_test
    })
