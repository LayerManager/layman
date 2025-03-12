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
from layman.util import url_for, get_publication_uuid, get_publication_info_by_uuid
from . import util
from .. import MAP_TYPE
from ..map_class import Map

MAP_SUBDIR = __name__.rsplit('.', maxsplit=1)[-1]
get_metadata_comparison = empty_method_returns_dict
pre_publication_action_check = empty_method
post_map = empty_method
patch_map = empty_method


def get_map_thumbnail_dir(publ_uuid):
    thumbnail_dir = os.path.join(util.get_map_dir(publ_uuid), 'thumbnail')
    return thumbnail_dir


def ensure_map_thumbnail_dir(publ_uuid):
    thumbnail_dir = get_map_thumbnail_dir(publ_uuid)
    pathlib.Path(thumbnail_dir).mkdir(parents=True, exist_ok=True)
    return thumbnail_dir


def get_map_info(workspace, mapname, *, x_forwarded_items=None):
    publ_uuid = get_publication_uuid(workspace, MAP_TYPE, mapname)
    return get_map_info_by_uuid(publ_uuid, workspace=workspace, mapname=mapname, x_forwarded_items=x_forwarded_items) \
        if publ_uuid else {}


def get_map_info_by_uuid(publ_uuid, *, workspace, mapname, x_forwarded_items=None):
    thumbnail_path = get_map_thumbnail_path(publ_uuid)
    if os.path.exists(thumbnail_path):
        return {
            'thumbnail': {
                'url': url_for('rest_workspace_map_thumbnail.get', workspace=workspace,
                               mapname=mapname, x_forwarded_items=x_forwarded_items),
                'path': os.path.relpath(thumbnail_path, settings.LAYMAN_DATA_DIR)
            },
            '_thumbnail': {
                'path': thumbnail_path,
            },
        }
    return {}


def delete_map(map: Map):
    util.delete_map_subdir(map.uuid, MAP_SUBDIR)


def get_map_thumbnail_path(publ_uuid):
    thumbnail_dir = get_map_thumbnail_dir(publ_uuid)
    return os.path.join(thumbnail_dir, publ_uuid + '.png')


def generate_map_thumbnail(publ_uuid, *, editor):
    map_info = get_publication_info_by_uuid(publ_uuid, context={'keys': ['file']})
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

    def show_timgen_logs(*, start_at_idx=0):
        layman_logs = browser.execute_script('''return window.layman_logs;''')
        current_app.logger.info(f"number of layman_logs: {len(layman_logs)}")
        for idx in range(start_at_idx, len(layman_logs)):
            layman_log = layman_logs[idx]
            current_app.logger.info(f"layman_log {idx+1}: {layman_log}")
        return len(layman_logs)

    max_attempts = 40
    attempts = 0
    data_url = browser.execute_script('''return window.canvas_data_url;''')
    data_url_error = browser.execute_script('''return window.canvas_data_url_error;''')
    already_shown_layman_logs = 0
    while data_url is None and data_url_error is None and attempts < max_attempts:
        current_app.logger.info(f"waiting for entries, data_url={data_url}, attempts={attempts}")
        already_shown_layman_logs = show_timgen_logs(start_at_idx=already_shown_layman_logs)
        time.sleep(0.5)
        attempts += 1
        data_url = browser.execute_script('''return window.canvas_data_url;''')
        data_url_error = browser.execute_script('''return window.canvas_data_url_error;''')

    show_timgen_logs(start_at_idx=already_shown_layman_logs)

    # browser.save_screenshot(f'/code/tmp/{workspace}.{mapname}.png')
    browser.close()
    browser.quit()

    if data_url_error:
        raise LaymanError(51, data={
            'reason': 'Error when requesting layer through WMS',
            'timgen_log': data_url_error,
        })

    if attempts >= max_attempts:
        current_app.logger.info(f"max attempts reach")
        current_app.logger.info(f"Map thumbnail: {publ_uuid}, editor={editor}")
        raise LaymanError(51, data="Max attempts reached when generating thumbnail")

    match = re.match(r'^data:image/png;base64,(.+)$', data_url)
    groups = match.groups()
    base64_image = groups[0]
    # current_app.logger.info(f"data_url {data_url}")
    # current_app.logger.info(f"len(data_url) {len(data_url)}")

    ensure_map_thumbnail_dir(publ_uuid)
    file_path = get_map_thumbnail_path(publ_uuid)
    try:
        os.remove(file_path)
    except OSError:
        pass

    with open(file_path, 'wb') as file:
        file.write(base64.b64decode(base64_image))
