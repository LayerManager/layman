import json
import time
import sys
import requests
import pytest
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

del sys.modules['layman']

from layman import app, settings
from layman.uuid import check_redis_consistency
from . import MAP_TYPE


@pytest.fixture(scope="module")
def client():
    # print('before app.test_client()')
    client = app.test_client()

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    # print('before app.app_context()')
    with app.app_context():
        yield client


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
@pytest.mark.usefixtures('ensure_layman', 'client')
def test_post_no_file(browser):
    check_redis_consistency(expected_publ_num_by_type={f'{MAP_TYPE}': 0})

    workspace = 'testuser2'
    client_url = settings.LAYMAN_CLIENT_URL

    response = requests.get(client_url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200

    browser.get(client_url)
    browser.set_window_size(1000, 2000)
    # browser.save_screenshot('/code/tmp/test-1.png')

    map_tab = browser.find_elements(By.CSS_SELECTOR, '.ui.attached.tabular.menu > a.item:nth-child(2)')
    assert len(map_tab) == 1
    map_tab = map_tab[0]
    map_tab.click()

    button = browser.find_elements(By.XPATH, '//button[text()="POST"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    user_input = browser.find_elements(By.NAME, 'Workspace')
    assert len(user_input) == 1
    user_input = user_input[0]
    user_input.clear()
    user_input.send_keys(workspace)

    button = browser.find_elements(By.XPATH, '//button[@type="submit"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    time.sleep(0.1)

    # browser.save_screenshot('/code/tmp/test-3.png')

    resp_negative_messages = browser.find_elements(By.CLASS_NAME, 'negative.message')
    assert len(resp_negative_messages) == 1
    resp_msg_div = resp_negative_messages[0].find_elements(By.CSS_SELECTOR, 'code')
    assert len(resp_msg_div) == 1
    resp_json = json.loads(resp_msg_div[0].text)
    assert resp_json['code'] == 1

    check_redis_consistency(expected_publ_num_by_type={f'{MAP_TYPE}': 0})
