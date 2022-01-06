import json
import time
import sys
import requests
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
@pytest.mark.usefixtures('ensure_layman', 'client')
def test_post_no_file(browser):
    check_redis_consistency(expected_publ_num_by_type={f'{MAP_TYPE}': 0})

    workspace = 'testuser2'
    client_url = settings.LAYMAN_CLIENT_URL

    response = requests.get(client_url)
    assert response.status_code == 200

    browser.get(client_url)
    browser.set_window_size(1000, 2000)
    # browser.save_screenshot('/code/tmp/test-1.png')

    map_tab = browser.find_elements_by_css_selector('.ui.attached.tabular.menu > a.item:nth-child(2)')
    assert len(map_tab) == 1
    map_tab = map_tab[0]
    map_tab.click()

    button = browser.find_elements_by_xpath('//button[text()="POST"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    user_input = browser.find_elements_by_name('Workspace')
    assert len(user_input) == 1
    user_input = user_input[0]
    user_input.clear()
    user_input.send_keys(workspace)

    button = browser.find_elements_by_xpath('//button[@type="submit"]')
    assert len(button) == 1
    button = button[0]
    button.click()

    time.sleep(0.1)

    # browser.save_screenshot('/code/tmp/test-3.png')

    resp_msg_div = browser.find_elements_by_css_selector(
        'div.ui.container > div:nth-child(8) > div.ui.segment > div.ui.negative.message > code')
    assert len(resp_msg_div) == 1
    resp_msg_div = resp_msg_div[0]
    resp_json = json.loads(resp_msg_div.text)
    assert resp_json['code'] == 1

    check_redis_consistency(expected_publ_num_by_type={f'{MAP_TYPE}': 0})
