import base64
import os
import pathlib
import re
import time
from urllib.parse import urlencode
from flask import current_app
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from layman import settings, LaymanError
from layman.authn import is_user_with_name
from layman.common import empty_method, empty_method_returns_dict
from layman.common.filesystem import util as common_util
from layman.util import url_for, get_publication_info
from . import util, input_file
from .. import MAP_TYPE

MAP_SUBDIR = __name__.split('.')[-1]
get_metadata_comparison = empty_method_returns_dict
pre_publication_action_check = empty_method
post_map = empty_method


def get_map_thumbnail_dir(workspace, mapname):
    thumbnail_dir = os.path.join(util.get_map_dir(workspace, mapname),
                                 'thumbnail')
    return thumbnail_dir


def ensure_map_thumbnail_dir(workspace, mapname):
    thumbnail_dir = get_map_thumbnail_dir(workspace, mapname)
    pathlib.Path(thumbnail_dir).mkdir(parents=True, exist_ok=True)
    return thumbnail_dir


def get_map_info(workspace, mapname):
    thumbnail_path = get_map_thumbnail_path(workspace, mapname)
    if os.path.exists(thumbnail_path):
        return {
            'thumbnail': {
                'url': url_for('rest_workspace_map_thumbnail.get', workspace=workspace,
                               mapname=mapname),
                'path': os.path.relpath(thumbnail_path, common_util.get_workspace_dir(workspace))
            },
            '_thumbnail': {
                'path': thumbnail_path,
            },
        }
    return {}


def patch_map(workspace, mapname, file_changed=True):
    if file_changed or not get_map_info(workspace, mapname):
        post_map(workspace, mapname)


get_publication_uuid = input_file.get_publication_uuid


def delete_map(workspace, mapname):
    util.delete_map_subdir(workspace, mapname, MAP_SUBDIR)


def get_map_thumbnail_path(workspace, mapname):
    thumbnail_dir = get_map_thumbnail_dir(workspace, mapname)
    return os.path.join(thumbnail_dir, mapname + '.png')


def generate_map_thumbnail(workspace, mapname, editor):
    map_info = get_publication_info(workspace, MAP_TYPE, mapname, context={'keys': ['file']})
    map_file_get_url = map_info['_file']['url']

    params = urlencode({
        'map_def_url': map_file_get_url,
        'gs_url': f"http://{settings.LAYMAN_SERVER_NAME}{settings.LAYMAN_GS_PATH}",
        'gs_public_url': f"{settings.LAYMAN_GS_PROXY_BASE_URL}",
        'editor': editor if is_user_with_name(editor) else '',
        'proxy_header': settings.LAYMAN_AUTHN_HTTP_HEADER_NAME,
        # 'file_name': tmp_file_name,
    })
    timgen_url = f"{settings.LAYMAN_TIMGEN_URL}?{params}"
    current_app.logger.info(f"Timgen URL: {timgen_url}")

    firefox_options = Options()
    firefox_options.headless = True
    desired_capabilities = DesiredCapabilities.FIREFOX
    desired_capabilities['loggingPrefs'] = {'browser': 'ALL'}
    browser = webdriver.Firefox(
        options=firefox_options,
        desired_capabilities=desired_capabilities,
    )
    browser.set_window_size(500, 500)

    browser.get(timgen_url)

    max_attempts = 40
    attempts = 0
    data_url = browser.execute_script('''return window.canvas_data_url;''')
    while data_url is None:
        current_app.logger.info(f"waiting for entries, data_url={data_url}")
        time.sleep(0.5)
        attempts += 1
        data_url = browser.execute_script('''return window.canvas_data_url;''')

    if attempts >= max_attempts:
        current_app.logger.info(f"max attempts reach")
        raise LaymanError(51, data="Max attempts reached when generating thumbnail")

    # browser.save_screenshot(f'/code/tmp/{workspace}.{mapname}.png')
    browser.close()
    browser.quit()

    match = re.match(r'^data:image/png;base64,(.+)$', data_url)
    groups = match.groups()
    base64_image = groups[0]
    # current_app.logger.info(f"data_url {data_url}")
    # current_app.logger.info(f"len(data_url) {len(data_url)}")

    ensure_map_thumbnail_dir(workspace, mapname)
    file_path = get_map_thumbnail_path(workspace, mapname)
    try:
        os.remove(file_path)
    except OSError:
        pass

    with open(file_path, 'wb') as file:
        file.write(base64.b64decode(base64_image))
