import time
import os
from test_tools import process_client
from test_tools.util import url_for
import requests
import pytest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from layman.layer.filesystem import input_chunk
from layman import settings, app


USERNAME = 'testuser1'
LAYERNAME = 'country_chunks'


@pytest.fixture(scope="module")
def clear_country_chunks():
    yield
    process_client.delete_workspace_layer(USERNAME, LAYERNAME, skip_404=True)


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
    chrome.set_window_size(1000, 2000)
    yield chrome
    chrome.close()
    chrome.quit()


@pytest.mark.test_client
@pytest.mark.usefixtures('ensure_layman', 'clear_country_chunks')
def test_post_layers_chunk(chrome):
    relative_file_paths = [
        'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
    ]
    file_paths = [os.path.join(os.getcwd(), fp) for fp in relative_file_paths]

    for file_path in file_paths:
        assert os.path.isfile(file_path)

    client_url = settings.LAYMAN_CLIENT_URL

    response = requests.get(client_url)
    assert response.status_code == 200

    chrome.get(client_url)
    chrome.set_window_size(1000, 2000)
    chrome.save_screenshot('/code/tmp/artifacts/client-post-layers-1.png')

    button = chrome.find_elements_by_xpath('//button[text()="POST"]')
    assert len(button) == 1
    button = button[0]
    button.click()
    chrome.save_screenshot('/code/tmp/artifacts/client-post-layers-1.5.png')

    user_input = chrome.find_elements_by_name('Workspace')
    assert len(user_input) == 1
    user_input = user_input[0]
    user_input.clear()
    user_input.send_keys(USERNAME)

    layername_input = chrome.find_elements_by_name('name')
    assert len(layername_input) == 1
    layername_input = layername_input[0]
    layername_input.clear()
    layername_input.send_keys(LAYERNAME)

    file_input = chrome.find_elements_by_name('file')
    assert len(file_input) == 1
    file_input = file_input[0]
    # print(" \n ".join(file_paths))
    file_input.send_keys(" \n ".join(file_paths))
    chrome.save_screenshot('/code/tmp/artifacts/client-post-layers-2.png')

    button = chrome.find_elements_by_xpath('//button[@type="submit"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    time.sleep(0.5)

    with app.app_context():
        layer_url = url_for('rest_workspace_layer.get', workspace=USERNAME, layername=LAYERNAME)
    response = requests.get(layer_url)
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file', 'metadata']
    max_attempts = 20
    attempts = 1
    while not (response.status_code == 200 and all(
            'status' not in response.json()[k] for k in keys_to_check
    )):
        # print('waiting')
        time.sleep(0.5)
        response = requests.get(layer_url)
        attempts += 1
        if attempts > max_attempts:
            chrome.save_screenshot('/code/tmp/artifacts/client-post-layers-2.5.png')
            raise Exception('Max attempts reached!')
    chrome.save_screenshot('/code/tmp/artifacts/client-post-layers-3.png')

    entries = chrome.get_log('browser')
    assert len(entries) > 3
    for entry in entries:
        # print(entry)
        assert entry['level'] == 'INFO' or (
            entry['level'] == 'SEVERE' and entry['message'].startswith(f'{client_url}rest/workspaces/{USERNAME}/layers/{LAYERNAME}/chunk?')
            and entry['message'].endswith(
                'Failed to load resource: the server responded with a status of 404 (NOT FOUND)')
        )
    total_chunks_key = input_chunk.get_layer_redis_total_chunks_key(USERNAME, LAYERNAME)
    assert not settings.LAYMAN_REDIS.exists(total_chunks_key)


@pytest.mark.test_client
@pytest.mark.usefixtures('ensure_layman', 'clear_country_chunks')
def test_patch_layer_chunk(chrome):
    relative_file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_populated_places.cpg',
        'tmp/naturalearth/110m/cultural/ne_110m_populated_places.dbf',
        'tmp/naturalearth/110m/cultural/ne_110m_populated_places.prj',
        'tmp/naturalearth/110m/cultural/ne_110m_populated_places.shp',
        'tmp/naturalearth/110m/cultural/ne_110m_populated_places.shx',
    ]
    file_paths = [os.path.join(os.getcwd(), fp) for fp in relative_file_paths]

    for file_path in file_paths:
        print('fp', file_path)
        assert os.path.isfile(file_path)

    client_url = settings.LAYMAN_CLIENT_URL

    response = requests.get(client_url)
    assert response.status_code == 200

    chrome.get(client_url)
    chrome.save_screenshot('/code/tmp/artifacts/client-patch-layers-1.png')

    button = chrome.find_elements_by_xpath('//button[text()="PATCH"]')
    assert len(button) == 1
    button = button[0]
    button.click()
    chrome.save_screenshot('/code/tmp/artifacts/client-patch-layers-2.png')

    user_input = chrome.find_elements_by_name('Workspace')
    assert len(user_input) == 1
    user_input = user_input[0]
    user_input.clear()
    user_input.send_keys(USERNAME)

    layername_input = chrome.find_elements_by_name('name')
    assert len(layername_input) == 1
    layername_input = layername_input[0]
    layername_input.clear()
    layername_input.send_keys(LAYERNAME)

    file_input = chrome.find_elements_by_name('file')
    assert len(file_input) == 1
    file_input = file_input[0]
    # print(" \n ".join(file_paths))
    file_input.send_keys(" \n ".join(file_paths))
    chrome.save_screenshot('/code/tmp/artifacts/client-patch-layers-3.png')

    button = chrome.find_elements_by_xpath('//button[@type="submit"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    time.sleep(0.5)

    with app.app_context():
        layer_url = url_for('rest_workspace_layer.get', workspace=USERNAME, layername=LAYERNAME)
    response = requests.get(layer_url)
    keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file', 'metadata']
    max_attempts = 20
    attempts = 1
    while not (response.status_code == 200 and all(
            'status' not in response.json()[k] for k in keys_to_check
    )):
        # print('waiting')
        time.sleep(0.5)
        response = requests.get(layer_url)
        attempts += 1
        if attempts > max_attempts:
            chrome.save_screenshot('/code/tmp/artifacts/client-patch-layers-3.5.png')
            raise Exception('Max attempts reached!')
    chrome.save_screenshot('/code/tmp/artifacts/client-patch-layers-4.png')

    entries = chrome.get_log('browser')
    assert len(entries) > 3, entries
    for entry in entries:
        print(entry)
        assert entry['level'] == 'INFO' or (
            entry['level'] == 'SEVERE'
            and entry['message'].startswith(
                f'{client_url}rest/{settings.REST_WORKSPACES_PREFIX}/{USERNAME}/layers/{LAYERNAME}/chunk?'
            ) and entry['message'].endswith('Failed to load resource: the server responded with a status of 404 (NOT FOUND)')
        )
    total_chunks_key = input_chunk.get_layer_redis_total_chunks_key(USERNAME, LAYERNAME)
    assert not settings.LAYMAN_REDIS.exists(total_chunks_key)
