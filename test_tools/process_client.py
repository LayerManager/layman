import io
import time
import os
import logging
import json
from functools import partial
from collections import namedtuple
import xml.etree.ElementTree as ET
import tempfile
import shutil
import requests

from geoserver import error as gs_error
from layman import app, settings, util as layman_util
from layman.layer.geoserver import wfs, wms
from layman.http import LaymanError
from test_tools.data import map as map_data
from . import util
from .util import url_for
from .process import LAYMAN_CELERY_QUEUE

logger = logging.getLogger(__name__)

ISS_URL_HEADER = 'AuthorizationIssUrl'
TOKEN_HEADER = 'Authorization'

layer_keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file', 'metadata']
map_keys_to_check = ['thumbnail', 'file', 'metadata']


LAYER_TYPE = 'layman.layer'
MAP_TYPE = 'layman.map'


PUBLICATION_TYPES = [
    LAYER_TYPE,
    MAP_TYPE,
]


PublicationTypeDef = namedtuple('PublicationTypeDef', ['url_param_name',
                                                       'get_publications_url',
                                                       'post_workspace_publication_url',
                                                       'patch_workspace_publication_url',
                                                       'get_workspace_publications_url',
                                                       'get_workspace_publication_url',
                                                       'delete_workspace_publication_url',
                                                       'delete_workspace_publications_url',
                                                       'keys_to_check',
                                                       'source_path',
                                                       'get_workspace_metadata_comparison_url',
                                                       'post_workspace_publication_chunk',
                                                       ])
PUBLICATION_TYPES_DEF = {MAP_TYPE: PublicationTypeDef('mapname',
                                                      'rest_maps.get',
                                                      'rest_workspace_maps.post',
                                                      'rest_workspace_map.patch',
                                                      'rest_workspace_maps.get',
                                                      'rest_workspace_map.get',
                                                      'rest_workspace_map.delete_map',
                                                      'rest_workspace_maps.delete',
                                                      map_keys_to_check,
                                                      'sample/layman.map/small_map.json',
                                                      'rest_workspace_map_metadata_comparison.get',
                                                      None,
                                                      ),
                         LAYER_TYPE: PublicationTypeDef('layername',
                                                        'rest_layers.get',
                                                        'rest_workspace_layers.post',
                                                        'rest_workspace_layer.patch',
                                                        'rest_workspace_layers.get',
                                                        'rest_workspace_layer.get',
                                                        'rest_workspace_layer.delete_layer',
                                                        'rest_workspace_layers.delete',
                                                        layer_keys_to_check,
                                                        'sample/layman.layer/small_layer.geojson',
                                                        'rest_workspace_layer_metadata_comparison.get',
                                                        'rest_workspace_layer_chunk.post',
                                                        ),
                         }

# pylint: disable=unexpected-keyword-arg
CompressTypeDef = namedtuple('CompressTypeDef', [
    'archive_name',
    'inner_directory',
    'file_name',
], defaults=[None, None, None])


def wait_for_rest(url, max_attempts, sleeping_time, check_response, headers=None):
    headers = headers or None
    response = requests.get(url, headers=headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)

    attempts = 1
    while not check_response(response):
        time.sleep(sleeping_time)
        response = requests.get(url, headers=headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
        attempts += 1
        if attempts > max_attempts:
            logger.error(f"r.status_code={response.status_code}\nrltest={response.text}")
            raise Exception('Max attempts reached!')


def raise_layman_error(response, status_codes_to_skip=None):
    status_codes_to_skip = status_codes_to_skip or set()
    status_codes_to_skip.add(200)
    if 400 <= response.status_code < 500 and response.status_code not in status_codes_to_skip:
        details = json.loads(response.text)
        raise LaymanError(details['code'],
                          details.get('detail'),
                          http_code=response.status_code,
                          sub_code=details.get('sub_code'))
    if response.status_code not in status_codes_to_skip:
        logger.error(f'raise_layman_error: response.status_code={response.status_code}, response.text={response.text}')
        response.raise_for_status()
    assert response.status_code in status_codes_to_skip, f"response.status_code={response.status_code}\nresponse.text={response.text}"
    assert 'Deprecation' not in response.headers, f'This is deprecated URL! Use new one. headers={response.headers}'


def upload_file_chunks(publication_type,
                       workspace,
                       name,
                       file_paths,
                       ):
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]
    time.sleep(0.5)
    with app.app_context():
        chunk_url = url_for(publication_type_def.post_workspace_publication_chunk,
                            workspace=workspace,
                            **{publication_type_def.url_param_name: name},
                            )

    file_chunks = [('file', file_name) for file_name in file_paths]
    file_dict = None
    for file_type, file_name in file_chunks:
        try:
            basename = os.path.basename(file_name)
            file_dict = {file_type: (basename, open(file_name, 'rb')), }
            data = {
                'file': basename,
                'resumableFilename': basename,
                'layman_original_parameter': file_type,
                'resumableChunkNumber': 1,
                'resumableTotalChunks': 1
            }

            chunk_response = requests.post(chunk_url,
                                           files=file_dict,
                                           data=data)
            raise_layman_error(chunk_response)
        finally:
            if file_dict:
                file_dict[file_type][1].close()


def patch_workspace_publication(publication_type,
                                workspace,
                                name,
                                *,
                                file_paths=None,
                                headers=None,
                                access_rights=None,
                                title=None,
                                style_file=None,
                                check_response_fn=None,
                                compress=False,
                                compress_settings=None,
                                with_chunks=False,
                                crs=None,
                                map_layers=None,
                                native_extent=None,
                                overview_resampling=None,
                                do_not_upload_chunks=False,
                                time_regex=None,
                                ):
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    # map layers must not be set together with file_paths
    assert not map_layers or not file_paths

    assert not (not with_chunks and do_not_upload_chunks)
    assert not (check_response_fn and do_not_upload_chunks)  # because check_response_fn is not called when do_not_upload_chunks

    file_paths = [] if file_paths is None and not map_layers else file_paths

    if style_file or with_chunks or compress or compress_settings or overview_resampling:
        assert publication_type == LAYER_TYPE
    if map_layers or native_extent:
        assert publication_type == MAP_TYPE

    # Compress settings can be used only with compress option
    assert not compress_settings or compress

    assert not (time_regex and publication_type == MAP_TYPE)
    assert not (publication_type == LAYER_TYPE and crs and not file_paths)

    with app.app_context():
        r_url = url_for(publication_type_def.patch_workspace_publication_url,
                        workspace=workspace,
                        **{publication_type_def.url_param_name: name})

    temp_dir = None
    if compress:
        temp_dir = tempfile.mkdtemp(prefix="layman_zip_")
        zip_file = util.compress_files(file_paths, compress_settings=compress_settings, output_dir=temp_dir)
        file_paths = [zip_file]

    if map_layers:
        temp_dir = tempfile.mkdtemp(prefix="layman_map_")
        file_path = os.path.join(temp_dir, name)
        map_data.create_map_with_internal_layers_file(map_layers, file_path=file_path, native_extent=native_extent,
                                                      native_crs=crs)
        file_paths = [file_path]

    for file_path in file_paths:
        assert os.path.isfile(file_path), file_path
    files = []
    try:
        data = dict()
        if not with_chunks:
            for file_path in file_paths:
                assert os.path.isfile(file_path), file_path
            files = [('file', (os.path.basename(fp), open(fp, 'rb'))) for fp in file_paths]
        else:
            data['file'] = [os.path.basename(file) for file in file_paths]
        if access_rights and access_rights.get('read'):
            data["access_rights.read"] = access_rights['read']
        if access_rights and access_rights.get('write'):
            data["access_rights.write"] = access_rights['write']
        if title:
            data['title'] = title
        if style_file:
            files.append(('style', (os.path.basename(style_file), open(style_file, 'rb'))))
        if overview_resampling:
            data['overview_resampling'] = overview_resampling
        if time_regex:
            data['time_regex'] = time_regex
        if publication_type == LAYER_TYPE and crs:
            data['crs'] = crs

        response = requests.patch(r_url,
                                  files=files,
                                  headers=headers,
                                  data=data)
        raise_layman_error(response)
    finally:
        for file_path in files:
            file_path[1][1].close()

    if with_chunks and not do_not_upload_chunks:
        upload_file_chunks(publication_type,
                           workspace,
                           name,
                           file_paths, )

    if not do_not_upload_chunks:
        wait_for_publication_status(workspace, publication_type, name, check_response_fn=check_response_fn, headers=headers)
    wfs.clear_cache(workspace)
    wms.clear_cache(workspace)
    if temp_dir:
        shutil.rmtree(temp_dir)
    return response.json()


patch_workspace_map = partial(patch_workspace_publication, MAP_TYPE)
patch_workspace_layer = partial(patch_workspace_publication, LAYER_TYPE)


def ensure_workspace_publication(publication_type,
                                 workspace,
                                 name,
                                 *,
                                 headers=None,
                                 access_rights=None,
                                 ):
    headers = headers or {}

    resposne = get_workspace_publications(publication_type, workspace, headers=headers, )
    publication_obj = next((publication for publication in resposne.json() if publication['name'] == name), None)
    if resposne.status_code == 200 and publication_obj:
        patch_needed = False
        if access_rights is not None:
            if 'read' in access_rights and set(access_rights['read'].split(',')) != set(publication_obj['access_rights']['read']):
                patch_needed = True
            if 'write' in access_rights and set(access_rights['write'].split(',')) != set(publication_obj['access_rights']['write']):
                patch_needed = True
        if patch_needed:
            result = patch_workspace_publication(publication_type, workspace, name, access_rights=access_rights, headers=headers)
        else:
            result = None
    else:
        result = publish_workspace_publication(publication_type, workspace, name, access_rights=access_rights, headers=headers)
    return result


ensure_workspace_layer = partial(ensure_workspace_publication, LAYER_TYPE)
ensure_workspace_map = partial(ensure_workspace_publication, MAP_TYPE)


def publish_workspace_publication(publication_type,
                                  workspace,
                                  name,
                                  *,
                                  file_paths=None,
                                  db_connection=None,
                                  headers=None,
                                  access_rights=None,
                                  title=None,
                                  style_file=None,
                                  description=None,
                                  check_response_fn=None,
                                  with_chunks=False,
                                  compress=False,
                                  compress_settings=None,
                                  crs=None,
                                  map_layers=None,
                                  native_extent=None,
                                  overview_resampling=None,
                                  do_not_upload_chunks=False,
                                  time_regex=None,
                                  do_not_post_name=False,
                                  ):
    title = title or name
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    assert not map_layers or not file_paths
    assert not map_layers or not db_connection

    assert not (not with_chunks and do_not_upload_chunks)
    assert not (check_response_fn and do_not_upload_chunks)  # because check_response_fn is not called when do_not_upload_chunks

    file_paths = [publication_type_def.source_path] if file_paths is None and db_connection is None and not map_layers else file_paths

    if style_file or with_chunks or compress or compress_settings or overview_resampling:
        assert publication_type == LAYER_TYPE
    if map_layers or native_extent:
        assert publication_type == MAP_TYPE

    # Compress settings can be used only with compress option
    assert not compress_settings or compress

    assert not (time_regex and publication_type == MAP_TYPE)

    with app.app_context():
        r_url = url_for(publication_type_def.post_workspace_publication_url, workspace=workspace)

    temp_dir = None
    if compress:
        temp_dir = tempfile.mkdtemp(prefix="layman_zip_")
        zip_file = util.compress_files(file_paths, compress_settings=compress_settings, output_dir=temp_dir)
        file_paths = [zip_file]

    if map_layers:
        temp_dir = tempfile.mkdtemp(prefix="layman_map_")
        file_path = os.path.join(temp_dir, name)
        map_data.create_map_with_internal_layers_file(map_layers, file_path=file_path, native_extent=native_extent,
                                                      native_crs=crs)
        file_paths = [file_path]

    files = []
    try:
        data = dict()
        if not do_not_post_name:
            data['name'] = name
            data['title'] = title
        if file_paths:
            if not with_chunks:
                for file_path in file_paths:
                    assert os.path.isfile(file_path), file_path
                files = [('file', (os.path.basename(fp), open(fp, 'rb'))) for fp in file_paths]
            else:
                data['file'] = [os.path.basename(file) for file in file_paths]
        if style_file:
            files.append(('style', (os.path.basename(style_file), open(style_file, 'rb'))))
        if access_rights and access_rights.get('read'):
            data["access_rights.read"] = access_rights['read']
        if access_rights and access_rights.get('write'):
            data["access_rights.write"] = access_rights['write']
        if description:
            data['description'] = description
        if crs and publication_type == LAYER_TYPE:
            data['crs'] = crs
        if overview_resampling:
            data['overview_resampling'] = overview_resampling
        if time_regex:
            data['time_regex'] = time_regex
        if db_connection:
            data['db_connection'] = db_connection
        response = requests.post(r_url,
                                 files=files,
                                 data=data,
                                 headers=headers)
        raise_layman_error(response)
        assert response.json()[0]['name'] == name or not name, f'name={name}, response.name={response.json()[0]["name"]}'
        name = name or response.json()[0]['name']

    finally:
        for file_path in files:
            file_path[1][1].close()

    if with_chunks and not do_not_upload_chunks:
        upload_file_chunks(publication_type,
                           workspace,
                           name,
                           file_paths, )

    if not do_not_upload_chunks:
        wait_for_publication_status(workspace, publication_type, name, check_response_fn=check_response_fn, headers=headers)
    if temp_dir:
        shutil.rmtree(temp_dir)
    return response.json()[0]


publish_workspace_map = partial(publish_workspace_publication, MAP_TYPE)
publish_workspace_layer = partial(publish_workspace_publication, LAYER_TYPE)


def get_workspace_publications_response(publication_type, workspace, *, headers=None, query_params=None, ):
    headers = headers or {}
    query_params = query_params or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.get_workspace_publications_url, workspace=workspace)
    response = requests.get(r_url, headers=headers, params=query_params)
    raise_layman_error(response)
    return response


def get_workspace_publications(publication_type, workspace, *, headers=None, query_params=None, ):
    return get_workspace_publications_response(publication_type, workspace, headers=headers, query_params=query_params,).json()


get_workspace_maps = partial(get_workspace_publications, MAP_TYPE)
get_workspace_layers = partial(get_workspace_publications, LAYER_TYPE)


def get_publications_response(publication_type, *, headers=None, query_params=None):
    headers = headers or {}
    query_params = query_params or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.get_publications_url)
    response = requests.get(r_url, headers=headers, params=query_params)
    raise_layman_error(response)
    return response


def get_publications(publication_type, *, headers=None, query_params=None):
    return get_publications_response(publication_type, headers=headers, query_params=query_params).json()


get_maps = partial(get_publications, MAP_TYPE)
get_layers = partial(get_publications, LAYER_TYPE)


def get_workspace_publication(publication_type, workspace, name, headers=None, ):
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.get_workspace_publication_url,
                        workspace=workspace,
                        **{publication_type_def.url_param_name: name})
    response = requests.get(r_url, headers=headers)
    raise_layman_error(response)
    return response.json()


get_workspace_map = partial(get_workspace_publication, MAP_TYPE)
get_workspace_layer = partial(get_workspace_publication, LAYER_TYPE)


def get_workspace_layer_style(workspace, layer, headers=None):
    with app.app_context():
        r_url = url_for('rest_workspace_layer_style.get',
                        workspace=workspace,
                        layername=layer)
    response = requests.get(r_url, headers=headers)
    raise_layman_error(response)
    return ET.parse(io.BytesIO(response.content))


def finish_delete(workspace, url, headers, skip_404=False, ):
    response = requests.delete(url, headers=headers)
    status_codes_to_skip = {404} if skip_404 else set()
    raise_layman_error(response, status_codes_to_skip)
    wfs.clear_cache(workspace)
    wms.clear_cache(workspace)
    return response.json()


def delete_workspace_publication(publication_type, workspace, name, *, headers=None, skip_404=False, ):
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.delete_workspace_publication_url,
                        workspace=workspace,
                        **{publication_type_def.url_param_name: name})

    return finish_delete(workspace, r_url, headers, skip_404=skip_404)


delete_workspace_map = partial(delete_workspace_publication, MAP_TYPE)
delete_workspace_layer = partial(delete_workspace_publication, LAYER_TYPE)


def delete_workspace_publications(publication_type, workspace, headers=None, ):
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.delete_workspace_publications_url,
                        workspace=workspace,
                        )

    return finish_delete(workspace, r_url, headers, )


delete_workspace_maps = partial(delete_workspace_publications, MAP_TYPE)
delete_workspace_layers = partial(delete_workspace_publications, LAYER_TYPE)


def assert_workspace_publications(publication_type, workspace, expected_publication_names, headers=None):
    response = get_workspace_publications(publication_type, workspace, headers=headers)
    publication_names = [li['name'] for li in response]
    assert set(publication_names) == set(expected_publication_names),\
        f"Publications {expected_publication_names} not equal to {response.text}. publication_type={publication_type}"


assert_workspace_layers = partial(assert_workspace_publications, LAYER_TYPE)
assert_workspace_maps = partial(assert_workspace_publications, MAP_TYPE)


def get_workspace_publication_metadata_comparison(publication_type, workspace, name, headers=None):
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]
    with app.app_context():
        r_url = url_for(publication_type_def.get_workspace_metadata_comparison_url, **{publication_type_def.url_param_name: name}, workspace=workspace)
    response = requests.get(r_url, headers=headers)
    raise_layman_error(response)
    return response.json()


get_workspace_layer_metadata_comparison = partial(get_workspace_publication_metadata_comparison, LAYER_TYPE)
get_workspace_map_metadata_comparison = partial(get_workspace_publication_metadata_comparison, MAP_TYPE)


def reserve_username(username, headers=None):
    headers = headers or {}
    with app.app_context():
        r_url = url_for('rest_current_user.patch')
    data = {
        'username': username,
    }
    response = requests.patch(r_url, headers=headers, data=data)
    raise_layman_error(response)
    claimed_username = response.json()['username']
    assert claimed_username == username


def get_current_user(headers=None):
    headers = headers or {}
    with app.app_context():
        r_url = url_for('rest_current_user.get')
    response = requests.get(r_url, headers=headers)
    response.raise_for_status()
    return response.json()


def ensure_reserved_username(username, headers=None):
    headers = headers or {}
    current_user = get_current_user(headers=headers)
    if 'username' not in current_user:
        reserve_username(username, headers=headers)
    else:
        assert current_user['username'] == username


def get_authz_headers(username):
    return {f'{ISS_URL_HEADER}': 'http://localhost:8082/o/oauth2/authorize',
            f'{TOKEN_HEADER}': f'Bearer {username}',
            }


def get_source_key_from_metadata_comparison(md_comparison, url_prefix):
    return next((
        k for k, v in md_comparison['metadata_sources'].items()
        if v['url'].startswith(url_prefix)
    ), None)


def post_wfst(xml, *, headers=None, url=None, workspace=None):
    assert not (url and workspace)
    rest_url = url or f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{workspace}/wfs?request=Transaction"\
        if workspace else f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/wfs?request=Transaction"
    headers = headers or dict()
    headers['Accept'] = 'text/xml'
    headers['Content-type'] = 'text/xml'

    response = requests.post(rest_url,
                             data=xml,
                             headers=headers)
    if response.status_code != 200:
        raise gs_error.Error(code_or_message='WFS-T error', data={'status_code': response.status_code})


def check_publication_status(response):
    try:
        current_status = response.json().get('layman_metadata', dict()).get('publication_status')
    except json.JSONDecodeError as exc:
        print(f'response={response.text}')
        raise exc
    return current_status in {'COMPLETE', 'INCOMPLETE'}


def wait_for_publication_status(workspace, publication_type, publication, *, check_response_fn=None, headers=None,):
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]
    with app.app_context():
        url = url_for(publication_type_def.get_workspace_publication_url,
                      workspace=workspace,
                      **{publication_type_def.url_param_name: publication})
    check_response_fn = check_response_fn or check_publication_status
    wait_for_rest(url, 60, 0.5, check_response=check_response_fn, headers=headers)


def patch_after_feature_change(workspace, publ_type, name):
    queue = LAYMAN_CELERY_QUEUE
    with app.app_context():
        layman_util.patch_after_feature_change(workspace, publ_type, name, queue=queue)
