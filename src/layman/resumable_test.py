import os
import time
from multiprocessing import Process

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from layman import app
import pytest


def test_resumable():
    username = 'testuser1'
    layername = 'country_chunks'
    file_paths = list(map(lambda fp: os.path.join(os.getcwd(), fp), [
        'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson',
    ]))
    for fp in file_paths:
        assert os.path.isfile(fp)

    port = 9002
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': port,
        'debug': False,
    })
    server.start()

    domain = "http://localhost:{}".format(port)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    desired_capabilities = DesiredCapabilities.CHROME
    desired_capabilities['loggingPrefs'] = {'browser': 'ALL'}
    chrome = webdriver.Chrome(
        chrome_options=chrome_options,
        desired_capabilities=desired_capabilities,
    )

    try:

        chrome.get(domain+'/static/test-client/index'
                          '.html')
        chrome.set_window_size(1000,2000)
        chrome.save_screenshot('/code/tmp/test-1.png')

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
        app.logger.info(" \n ".join(file_paths))
        file_input.send_keys(" \n ".join(file_paths))
        chrome.save_screenshot('/code/tmp/test-2.png')

        button = chrome.find_elements_by_xpath('//button[@type="submit"]')
        assert len(button) == 1
        button = button[0]
        button.click()

        layer_url = '{}/rest/{}/layers/{}?'.format(
                        domain, username, layername
                    )
        import requests
        r = requests.get(layer_url)
        keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file']
        max_attempts = 40
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
        chrome.save_screenshot('/code/tmp/test-3.png')

        entries = chrome.get_log('browser')
        assert len(entries) > 3
        for entry in entries:
            # print(entry)
            assert entry['level'] == 'INFO' or (
                entry['level'] == 'SEVERE'
                and entry['message'].startswith(
                    '{}/rest/{}/layers/{}/chunk?'.format(
                        domain, username, layername
                    )
                ) and entry['message'].endswith('Failed to load resource: the server responded with a status of 404 (NOT FOUND)')
            )

    except Exception as e:
        assert 1==2
    finally:
        chrome.close()
        chrome.quit()

        server.terminate()
        server.join()
