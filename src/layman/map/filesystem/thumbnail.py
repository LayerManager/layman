import base64
import os
import pathlib
import re
import time
from urllib.parse import urlencode
from flask import current_app
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import \
    DesiredCapabilities

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


def get_map_thumbnail_dir(username, mapname):
    thumbnail_dir = os.path.join(util.get_map_dir(username, mapname),
                                 'thumbnail')
    return thumbnail_dir


def ensure_map_thumbnail_dir(username, mapname):
    thumbnail_dir = get_map_thumbnail_dir(username, mapname)
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
            }
        }
    return {}


def patch_map(workspace, mapname, file_changed=True):
    if file_changed or not get_map_info(workspace, mapname):
        post_map(workspace, mapname)


get_publication_uuid = input_file.get_publication_uuid


def delete_map(workspace, mapname):
    util.delete_map_subdir(workspace, mapname, MAP_SUBDIR)


def get_map_thumbnail_path(username, mapname):
    thumbnail_dir = get_map_thumbnail_dir(username, mapname)
    return os.path.join(thumbnail_dir, mapname + '.png')


def generate_map_thumbnail(username, mapname, editor):
    map_info = get_publication_info(username, MAP_TYPE, mapname, context={'keys': ['file']})
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

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    desired_capabilities = DesiredCapabilities.CHROME
    desired_capabilities['goog:loggingPrefs'] = {'browser': 'ALL'}
    chrome = webdriver.Chrome(
        options=chrome_options,
        desired_capabilities=desired_capabilities,
    )
    chrome.set_window_size(500, 500)

    chrome.get(timgen_url)
    entries = chrome.get_log('browser')
    max_attempts = 40
    attempts = 0
    while next((e for e in entries
                if (e['level'] == 'INFO' and '"dataurl" "data:image/png;base64,' in e['message'])
                or (e.get('level') == 'SEVERE' and e.get('source') == 'javascript')
                ), None) is None and attempts < max_attempts:
        current_app.logger.info(f"waiting for entries")
        time.sleep(0.5)
        attempts += 1
        entries = chrome.get_log('browser')
    if attempts >= max_attempts:
        current_app.logger.info(f"max attempts reach")
        raise LaymanError(51, data="Max attempts reached when generating thumbnail")
    for entry in entries:
        if entry.get('level') == 'SEVERE' and entry.get('source') == 'javascript':
            current_app.logger.error(f"timgen error {entry}")
            raise LaymanError(51, private_data=entry)
        current_app.logger.info(f"browser entry {entry}")

    # chrome.save_screenshot(f'/code/tmp/{username}.{mapname}.png')
    chrome.close()
    chrome.quit()

    entry = next((e for e in entries if e['level'] == 'INFO' and '"dataurl" "data:image/png;base64,' in e['message']),
                 None)
    assert entry is not None
    match = re.match(r'.*\"dataurl\" \"data:image/png;base64,(.+)\"', entry['message'])
    assert match
    groups = match.groups()
    assert len(groups) >= 1
    data_url = groups[0]
    # current_app.logger.info(f"data_url {data_url}")
    # current_app.logger.info(f"len(data_url) {len(data_url)}")

    ensure_map_thumbnail_dir(username, mapname)
    file_path = get_map_thumbnail_path(username, mapname)
    try:
        os.remove(file_path)
    except OSError:
        pass

    with open(file_path, 'wb') as file:
        file.write(base64.b64decode(data_url))
