import json
import os
import requests
import pytest

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
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
def browser():
    firefox_options = Options()
    firefox_options.headless = True
    desired_capabilities = DesiredCapabilities.FIREFOX
    desired_capabilities['loggingPrefs'] = {'browser': 'ALL'}
    firefox = webdriver.Firefox(
        options=firefox_options,
        desired_capabilities=desired_capabilities,
    )
    firefox.set_window_size(1000, 2000)
    yield firefox
    firefox.close()
    firefox.quit()


@pytest.mark.test_client
@pytest.mark.usefixtures('ensure_layman', 'clear_country_chunks')
def test_post_layers_chunk(browser):
    relative_file_paths = [
        'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
    ]
    file_paths = [os.path.join(os.getcwd(), fp) for fp in relative_file_paths]

    for file_path in file_paths:
        assert os.path.isfile(file_path)

    client_url = settings.LAYMAN_CLIENT_URL

    response = requests.get(client_url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200

    browser.get(client_url)
    browser.set_window_size(1000, 2000)
    browser.save_screenshot('/code/tmp/artifacts/client-post-layers-1.png')

    button = browser.find_elements(By.XPATH, '//button[text()="POST"]')
    assert len(button) == 1
    button = button[0]
    button.click()
    browser.save_screenshot('/code/tmp/artifacts/client-post-layers-1.5.png')

    user_input = browser.find_elements(By.NAME, 'Workspace')
    assert len(user_input) == 1
    user_input = user_input[0]
    user_input.clear()
    user_input.send_keys(WORKSPACE)

    layername_input = browser.find_elements(By.NAME, 'name')
    assert len(layername_input) == 1
    layername_input = layername_input[0]
    layername_input.clear()
    layername_input.send_keys(LAYERNAME)

    file_input = browser.find_elements(By.NAME, 'file')
    assert len(file_input) == 1
    file_input = file_input[0]
    for file_path in file_paths:
        file_input.send_keys(file_path)
    browser.save_screenshot('/code/tmp/artifacts/client-post-layers-2.png')

    button = browser.find_elements(By.XPATH, '//button[@type="submit"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    try:
        process_client.wait_for_publication_status(WORKSPACE,
                                                   process_client.LAYER_TYPE,
                                                   LAYERNAME)
    except Exception as exc:
        browser.save_screenshot('/code/tmp/artifacts/client-post-layers-2.5.png')
        raise exc
    browser.save_screenshot('/code/tmp/artifacts/client-post-layers-3.png')

    positive_response = browser.find_elements(By.XPATH, '//div[@class="ui positive message"]')
    assert positive_response

    resp_positive_messages = browser.find_elements(By.CLASS_NAME, 'positive.message')
    assert len(resp_positive_messages) == 2
    resp_msg = resp_positive_messages[0]
    assert resp_msg.text == 'Upload finished!'
    resp_msg_div = resp_positive_messages[1].find_elements(By.CSS_SELECTOR, 'code')
    assert len(resp_msg_div) == 1
    resp_json = json.loads(resp_msg_div[0].text)
    assert resp_json[0]['name'] == LAYERNAME

    total_chunks_key = input_chunk.get_layer_redis_total_chunks_key(WORKSPACE, LAYERNAME)
    assert not settings.LAYMAN_REDIS.exists(total_chunks_key)


@pytest.mark.test_client
@pytest.mark.usefixtures('ensure_layman', 'clear_country_chunks')
def test_patch_layer_chunk(browser):
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

    response = requests.get(client_url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200

    browser.get(client_url)
    browser.save_screenshot('/code/tmp/artifacts/client-patch-layers-1.png')

    button = browser.find_elements(By.XPATH, '//button[text()="PATCH"]')
    assert len(button) == 1
    button = button[0]
    button.click()
    browser.save_screenshot('/code/tmp/artifacts/client-patch-layers-2.png')

    user_input = browser.find_elements(By.NAME, 'Workspace')
    assert len(user_input) == 1
    user_input = user_input[0]
    user_input.clear()
    user_input.send_keys(WORKSPACE)

    layername_input = browser.find_elements(By.NAME, 'name')
    assert len(layername_input) == 1
    layername_input = layername_input[0]
    layername_input.clear()
    layername_input.send_keys(LAYERNAME)

    file_input = browser.find_elements(By.NAME, 'file')
    assert len(file_input) == 1
    file_input = file_input[0]
    for file_path in file_paths:
        file_input.send_keys(file_path)
    browser.save_screenshot('/code/tmp/artifacts/client-patch-layers-3.png')

    button = browser.find_elements(By.XPATH, '//button[@type="submit"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    try:
        process_client.wait_for_publication_status(WORKSPACE,
                                                   process_client.LAYER_TYPE,
                                                   LAYERNAME)
    except Exception as exc:
        browser.save_screenshot('/code/tmp/artifacts/client-patch-layers-3.5.png')
        raise exc
    browser.save_screenshot('/code/tmp/artifacts/client-patch-layers-4.png')

    positive_response = browser.find_elements(By.XPATH, '//div[@class="ui positive message"]')
    assert positive_response

    resp_positive_messages = browser.find_elements(By.CLASS_NAME, 'positive.message')
    assert len(resp_positive_messages) == 2
    resp_msg = resp_positive_messages[0]
    assert resp_msg.text == 'Upload finished!'
    resp_msg_div = resp_positive_messages[1].find_elements(By.CSS_SELECTOR, 'code')
    assert len(resp_msg_div) == 1
    resp_json = json.loads(resp_msg_div[0].text)
    assert resp_json['name'] == LAYERNAME

    total_chunks_key = input_chunk.get_layer_redis_total_chunks_key(WORKSPACE, LAYERNAME)
    assert not settings.LAYMAN_REDIS.exists(total_chunks_key)
