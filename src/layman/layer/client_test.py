import os
import requests
import pytest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from layman.layer.filesystem import input_chunk
from layman import settings
from test_tools import process_client


WORKSPACE = 'test_layer_client_test_workspace'
LAYERNAME = 'country_chunks'


@pytest.fixture(scope="module")
def clear_country_chunks():
    yield
    process_client.delete_workspace_layer(WORKSPACE, LAYERNAME, skip_404=True)


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
    user_input.send_keys(WORKSPACE)

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

    try:
        process_client.wait_for_publication_status(WORKSPACE,
                                                   process_client.LAYER_TYPE,
                                                   LAYERNAME)
    except Exception as exc:
        chrome.save_screenshot('/code/tmp/artifacts/client-post-layers-2.5.png')
        raise exc
    chrome.save_screenshot('/code/tmp/artifacts/client-post-layers-3.png')

    entries = chrome.get_log('browser')
    assert len(entries) > 3
    for entry in entries:
        # print(entry)
        assert entry['level'] == 'INFO' or (
            entry['level'] == 'SEVERE' and entry['message'].startswith(f'{client_url}rest/workspaces/{WORKSPACE}/layers/{LAYERNAME}/chunk?')
            and entry['message'].endswith(
                'Failed to load resource: the server responded with a status of 404 (NOT FOUND)')
        )
    total_chunks_key = input_chunk.get_layer_redis_total_chunks_key(WORKSPACE, LAYERNAME)
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
    user_input.send_keys(WORKSPACE)

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

    try:
        process_client.wait_for_publication_status(WORKSPACE,
                                                   process_client.LAYER_TYPE,
                                                   LAYERNAME)
    except Exception as exc:
        chrome.save_screenshot('/code/tmp/artifacts/client-patch-layers-3.5.png')
        raise exc
    chrome.save_screenshot('/code/tmp/artifacts/client-patch-layers-4.png')

    entries = chrome.get_log('browser')
    assert len(entries) > 3, entries
    for entry in entries:
        print(entry)
        assert entry['level'] == 'INFO' or (
            entry['level'] == 'SEVERE'
            and entry['message'].startswith(
                f'{client_url}rest/{settings.REST_WORKSPACES_PREFIX}/{WORKSPACE}/layers/{LAYERNAME}/chunk?'
            ) and entry['message'].endswith('Failed to load resource: the server responded with a status of 404 (NOT FOUND)')
        )
    total_chunks_key = input_chunk.get_layer_redis_total_chunks_key(WORKSPACE, LAYERNAME)
    assert not settings.LAYMAN_REDIS.exists(total_chunks_key)
