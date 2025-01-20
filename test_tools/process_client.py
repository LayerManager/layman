import io
import time
import os
import logging
import json
from contextlib import ExitStack
from functools import partial
from collections import namedtuple
import xml.etree.ElementTree as ET
import tempfile
import shutil
import requests

from geoserver import error as gs_error
from layman import app, settings, util as layman_util, names
from layman.layer.geoserver import wfs, wms
from layman.http import LaymanError
from test_tools.data import map as map_data
from . import util
from .util import url_for
from .process import LAYMAN_CELERY_QUEUE

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 15

TOKEN_HEADER = 'Authorization'

layer_keys_to_check = ['db', 'wms', 'wfs', 'thumbnail', 'file', 'metadata']
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
                                                       'get_workspace_publication_thumbnail_url',
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
                                                      'rest_workspace_map_thumbnail.get',
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
                                                        'rest_workspace_layer_thumbnail.get',
                                                        'rest_workspace_layer.delete_layer',
                                                        'rest_workspace_layers.delete',
                                                        layer_keys_to_check,
                                                        'sample/layman.layer/small_layer.geojson',
                                                        'rest_workspace_layer_metadata_comparison.get',
                                                        'rest_workspace_layer_chunk.post',
                                                        ),
                         None: PublicationTypeDef('publicationname',
                                                  'rest_publications.get',
                                                  None,
                                                  None,
                                                  None,
                                                  None,
                                                  None,
                                                  None,
                                                  None,
                                                  None,
                                                  None,
                                                  None,
                                                  None,
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
    return response


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


def raise_if_not_complete_status(response):
    resp_json = response.json()
    status = resp_json.get('layman_metadata', {}).get('publication_status')
    if status != 'COMPLETE':
        failed_source_key = next((k for k, v in resp_json.items() if isinstance(v, dict) and v.get('status') == 'FAILURE'), None)
        if failed_source_key and resp_json[failed_source_key].get('error', {}).get('code'):
            failed_source = resp_json[failed_source_key]
            error_desc = failed_source['error']
            raise LaymanError(error_desc['code'],
                              error_desc.get('detail'),
                              sub_code=error_desc.get('sub_code'))
        raise LaymanError(55, data=resp_json)


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
    for file_type, file_name in file_chunks:
        basename = os.path.basename(file_name)
        data = {
            'file': basename,
            'resumableFilename': basename,
            'layman_original_parameter': file_type,
            'resumableChunkNumber': 1,
            'resumableTotalChunks': 1
        }
        with open(file_name, 'rb') as file:
            file_dict = {file_type: (basename, file), }
            chunk_response = requests.post(chunk_url,
                                           files=file_dict,
                                           data=data,
                                           timeout=HTTP_TIMEOUT,
                                           )
        raise_layman_error(chunk_response)


def patch_workspace_publication(publication_type,
                                workspace,
                                name,
                                *,
                                file_paths=None,
                                external_table_uri=None,
                                headers=None,
                                actor_name=None,
                                access_rights=None,
                                title=None,
                                style_file=None,
                                check_response_fn=None,
                                raise_if_not_complete=True,
                                compress=False,
                                compress_settings=None,
                                with_chunks=False,
                                crs=None,
                                map_layers=None,
                                native_extent=None,
                                overview_resampling=None,
                                do_not_upload_chunks=False,
                                time_regex=None,
                                time_regex_format=None,
                                skip_asserts=False,
                                ):
    headers = headers or {}
    if actor_name:
        assert TOKEN_HEADER not in headers
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    if not skip_asserts:
        # map layers must not be set together with file_paths
        assert not map_layers or not file_paths
        assert not map_layers or not external_table_uri

        assert not (not with_chunks and do_not_upload_chunks)
        assert not (check_response_fn and do_not_upload_chunks)  # because check_response_fn is not called when do_not_upload_chunks
        assert not (raise_if_not_complete and do_not_upload_chunks)
        assert not (check_response_fn and raise_if_not_complete)

        assert not (time_regex and publication_type == MAP_TYPE)
        assert not (publication_type == LAYER_TYPE and crs and not file_paths)

        if style_file or with_chunks or compress or compress_settings or overview_resampling:
            assert publication_type == LAYER_TYPE
        if map_layers or native_extent:
            assert publication_type == MAP_TYPE

        # Compress settings can be used only with compress option
        assert not compress_settings or compress

    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))

    file_paths = [] if file_paths is None and not map_layers else file_paths

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
    with ExitStack() as stack:
        data = {}
        if not with_chunks:
            for file_path in file_paths:
                assert os.path.isfile(file_path), file_path
            files = [('file', (os.path.basename(fp), stack.enter_context(open(fp, 'rb')))) for fp in file_paths]
        else:
            data['file'] = [os.path.basename(file) for file in file_paths]
        if access_rights and access_rights.get('read'):
            data["access_rights.read"] = access_rights['read']
        if access_rights and access_rights.get('write'):
            data["access_rights.write"] = access_rights['write']
        if title:
            data['title'] = title
        if style_file:
            files.append(('style', (os.path.basename(style_file), stack.enter_context(open(style_file, 'rb')))))
        if overview_resampling:
            data['overview_resampling'] = overview_resampling
        if time_regex:
            data['time_regex'] = time_regex
        if time_regex_format:
            data['time_regex_format'] = time_regex_format
        if publication_type == LAYER_TYPE and crs:
            data['crs'] = crs
        if external_table_uri:
            data['external_table_uri'] = external_table_uri

        response = requests.patch(r_url,
                                  files=files,
                                  headers=headers,
                                  data=data,
                                  timeout=HTTP_TIMEOUT,
                                  )
    raise_layman_error(response)

    assert response.json()['name'] == name or not name, f'name={name}, response.name={response.json()[0]["name"]}'
    expected_resp_keys = ['name', 'uuid', 'url']
    if with_chunks:
        expected_resp_keys.append('files_to_upload')
    assert all(key in response.json() for key in expected_resp_keys), f'name={name}, response.name={response.json()[0]["name"]}'

    if with_chunks and not do_not_upload_chunks:
        upload_file_chunks(publication_type,
                           workspace,
                           name,
                           file_paths, )

    if not do_not_upload_chunks:
        wait_for_publication_status(workspace, publication_type, name, check_response_fn=check_response_fn,
                                    headers=headers, raise_if_not_complete=raise_if_not_complete)
    wfs.clear_cache()
    wms.clear_cache()
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

    response = get_publications(publication_type, workspace=workspace, headers=headers, )
    publication_obj = next((publication for publication in response.json() if publication['name'] == name), None)
    if response.status_code == 200 and publication_obj:
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
                                  uuid=None,
                                  file_paths=None,
                                  external_table_uri=None,
                                  headers=None,
                                  actor_name=None,
                                  access_rights=None,
                                  title=None,
                                  style_file=None,
                                  description=None,
                                  check_response_fn=None,
                                  raise_if_not_complete=True,
                                  with_chunks=False,
                                  compress=False,
                                  compress_settings=None,
                                  crs=None,
                                  map_layers=None,
                                  native_extent=None,
                                  overview_resampling=None,
                                  do_not_upload_chunks=False,
                                  time_regex=None,
                                  time_regex_format=None,
                                  do_not_post_name=False,
                                  ):
    title = title or name
    headers = headers or {}
    if actor_name:
        assert TOKEN_HEADER not in headers
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    assert not map_layers or not file_paths
    assert not map_layers or not external_table_uri

    assert not (not with_chunks and do_not_upload_chunks)
    assert not (check_response_fn and do_not_upload_chunks)  # because check_response_fn is not called when do_not_upload_chunks
    assert not (raise_if_not_complete and do_not_upload_chunks)
    assert not (check_response_fn and raise_if_not_complete)

    file_paths = [publication_type_def.source_path] if file_paths is None and external_table_uri is None and not map_layers else file_paths

    if style_file or with_chunks or compress or compress_settings or overview_resampling:
        assert publication_type == LAYER_TYPE
    if map_layers or native_extent:
        assert publication_type == MAP_TYPE

    # Compress settings can be used only with compress option
    assert not compress_settings or compress

    assert not (time_regex and publication_type == MAP_TYPE)

    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))

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
    with ExitStack() as stack:
        data = {}
        if uuid:
            data["uuid"] = uuid
        if not do_not_post_name:
            data['name'] = name
            data['title'] = title
        if file_paths:
            if not with_chunks:
                for file_path in file_paths:
                    assert os.path.isfile(file_path), file_path
                files = [('file', (os.path.basename(fp), stack.enter_context(open(fp, 'rb')))) for fp in file_paths]
            else:
                data['file'] = [os.path.basename(file) for file in file_paths]
        if style_file:
            files.append(('style', (os.path.basename(style_file), stack.enter_context(open(style_file, 'rb')))))
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
        if time_regex_format:
            data['time_regex_format'] = time_regex_format
        if external_table_uri:
            data['external_table_uri'] = external_table_uri
        response = requests.post(r_url,
                                 files=files,
                                 data=data,
                                 headers=headers,
                                 timeout=HTTP_TIMEOUT,
                                 )
    raise_layman_error(response)
    assert response.json()[0]['name'] == name or not name, f'name={name}, response.name={response.json()[0]["name"]}'
    name = name or response.json()[0]['name']

    if with_chunks and not do_not_upload_chunks:
        upload_file_chunks(publication_type,
                           workspace,
                           name,
                           file_paths, )

    if not do_not_upload_chunks:
        wait_for_publication_status(workspace, publication_type, name, check_response_fn=check_response_fn,
                                    headers=headers, raise_if_not_complete=raise_if_not_complete)
    if temp_dir:
        shutil.rmtree(temp_dir)
    return response.json()[0]


publish_workspace_map = partial(publish_workspace_publication, MAP_TYPE)
publish_workspace_layer = partial(publish_workspace_publication, LAYER_TYPE)

GET_PUBLICATIONS_KNOWN_PARAMS = {'full_text_filter', 'bbox_filter', 'bbox_filter_crs', 'order_by', 'ordering_bbox',
                                 'ordering_bbox_crs', 'limit', 'offset'}


def get_workspace_publications_response(publication_type, workspace, *, headers=None, query_params=None, ):
    query_params = query_params or {}
    assert set(query_params.keys()) <= GET_PUBLICATIONS_KNOWN_PARAMS, \
        f"Unknown params: {set(query_params.keys()) - GET_PUBLICATIONS_KNOWN_PARAMS}"
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.get_workspace_publications_url, workspace=workspace)
    response = requests.get(r_url, headers=headers, params=query_params, timeout=HTTP_TIMEOUT)
    raise_layman_error(response)
    return response


def get_publications_response(publication_type, *, workspace=None, headers=None, query_params=None):
    assert publication_type or not workspace
    query_params = query_params or {}
    assert set(query_params.keys()) <= GET_PUBLICATIONS_KNOWN_PARAMS, \
        f"Unknown params: {set(query_params.keys()) - GET_PUBLICATIONS_KNOWN_PARAMS}"
    headers = headers or {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.get_workspace_publications_url, workspace=workspace) if workspace else url_for(publication_type_def.get_publications_url)
    response = requests.get(r_url, headers=headers, params=query_params, timeout=HTTP_TIMEOUT)
    raise_layman_error(response)
    return response


def get_publications(publication_type, *, workspace=None, headers=None, query_params=None, actor_name=None):
    headers = headers or {}
    if actor_name:
        assert TOKEN_HEADER not in headers
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))
    return get_publications_response(publication_type, workspace=workspace, headers=headers, query_params=query_params).json()


get_maps = partial(get_publications, MAP_TYPE)
get_layers = partial(get_publications, LAYER_TYPE)


def get_workspace_publication(publication_type, workspace, name, headers=None, *, actor_name=None):
    headers = headers or {}
    if actor_name:
        assert TOKEN_HEADER not in headers
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))

    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.get_workspace_publication_url,
                        workspace=workspace,
                        **{publication_type_def.url_param_name: name})
    response = requests.get(r_url, headers=headers, timeout=HTTP_TIMEOUT)
    raise_layman_error(response)
    return response.json()


get_workspace_map = partial(get_workspace_publication, MAP_TYPE)
get_workspace_layer = partial(get_workspace_publication, LAYER_TYPE)


def get_workspace_layer_style(workspace, layer, headers=None, *, actor_name=None, ):
    headers = headers or {}
    if actor_name:
        assert TOKEN_HEADER not in headers
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))
    with app.app_context():
        r_url = url_for('rest_workspace_layer_style.get',
                        workspace=workspace,
                        layername=layer)
    response = requests.get(r_url, headers=headers, timeout=HTTP_TIMEOUT)
    raise_layman_error(response)
    return ET.parse(io.BytesIO(response.content))


def finish_delete(url, headers, skip_404=False, ):
    response = requests.delete(url, headers=headers, timeout=HTTP_TIMEOUT)
    status_codes_to_skip = {404} if skip_404 else set()
    raise_layman_error(response, status_codes_to_skip)
    wfs.clear_cache()
    wms.clear_cache()
    return response.json()


def delete_workspace_publication(publication_type, workspace, name, *, headers=None, skip_404=False, actor_name=None, ):
    headers = headers or {}
    if actor_name:
        assert TOKEN_HEADER not in headers
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))

    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.delete_workspace_publication_url,
                        workspace=workspace,
                        **{publication_type_def.url_param_name: name})

    return finish_delete(r_url, headers, skip_404=skip_404)


delete_workspace_map = partial(delete_workspace_publication, MAP_TYPE)
delete_workspace_layer = partial(delete_workspace_publication, LAYER_TYPE)


def delete_workspace_publications(publication_type, workspace, headers=None, *, actor_name=None, ):
    headers = headers or {}
    if actor_name:
        assert TOKEN_HEADER not in headers
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]

    with app.app_context():
        r_url = url_for(publication_type_def.delete_workspace_publications_url,
                        workspace=workspace,
                        )

    return finish_delete(r_url, headers, )


delete_workspace_maps = partial(delete_workspace_publications, MAP_TYPE)
delete_workspace_layers = partial(delete_workspace_publications, LAYER_TYPE)


def assert_workspace_publications(publication_type, workspace, expected_publication_names, headers=None):
    response = get_publications(publication_type, workspace=workspace, headers=headers)
    publication_names = [li['name'] for li in response]
    assert set(publication_names) == set(expected_publication_names), \
        f"Publications {expected_publication_names} not equal to {response.text}. publication_type={publication_type}"


assert_workspace_layers = partial(assert_workspace_publications, LAYER_TYPE)
assert_workspace_maps = partial(assert_workspace_publications, MAP_TYPE)


def get_workspace_publication_metadata_comparison(publication_type, workspace, name, headers=None, actor_name=None):
    headers = headers or {}
    if actor_name:
        assert TOKEN_HEADER not in headers

    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))

    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]
    with app.app_context():
        r_url = url_for(publication_type_def.get_workspace_metadata_comparison_url, **{publication_type_def.url_param_name: name}, workspace=workspace)
    response = requests.get(r_url, headers=headers, timeout=HTTP_TIMEOUT)
    raise_layman_error(response)
    return response.json()


get_workspace_layer_metadata_comparison = partial(get_workspace_publication_metadata_comparison, LAYER_TYPE)
get_workspace_map_metadata_comparison = partial(get_workspace_publication_metadata_comparison, MAP_TYPE)


def reserve_username(username, headers=None, *, actor_name=None):
    headers = headers or {}
    if actor_name:
        assert TOKEN_HEADER not in headers

    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))
    with app.app_context():
        r_url = url_for('rest_current_user.patch')
    data = {
        'username': username,
    }
    response = requests.patch(r_url, headers=headers, data=data, timeout=HTTP_TIMEOUT)
    raise_layman_error(response)
    claimed_username = response.json()['username']
    assert claimed_username == username


def get_current_user(headers=None):
    headers = headers or {}
    with app.app_context():
        r_url = url_for('rest_current_user.get')
    response = requests.get(r_url, headers=headers, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    return response.json()


def ensure_reserved_username(username, headers=None):
    headers = get_authz_headers(username) if headers is None else headers
    current_user = get_current_user(headers=headers)
    if 'username' not in current_user:
        reserve_username(username, headers=headers)
    else:
        assert current_user['username'] == username


def get_authz_headers(username):
    return {f'{TOKEN_HEADER}': f'Bearer {username}',
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
    headers = headers or {}
    headers['Accept'] = 'text/xml'
    headers['Content-type'] = 'text/xml'

    response = requests.post(rest_url,
                             data=xml,
                             headers=headers,
                             timeout=HTTP_TIMEOUT,
                             )
    if response.headers.get('content-type') == 'application/json':
        raise_layman_error(response)
    if response.status_code != 200:
        logger.info(f"GeoServer error response:\n{response.text}")
        raise gs_error.Error(code_or_message='WFS-T error', data={'status_code': response.status_code})


def post_wfst_with_xml_getter(workspace, layer, *, xml_getter, actor_name=None, xml_getter_params=None):
    xml_getter_params = xml_getter_params or {}
    headers = {}
    if actor_name:
        assert TOKEN_HEADER not in headers

    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))

    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, LAYER_TYPE, layer)
    gs_layername = names.get_layer_names_by_source(uuid=uuid, ).wfs

    xml = xml_getter(gs_layername.workspace, gs_layername.name, **xml_getter_params)
    post_wfst(xml, headers=headers, workspace=workspace)


def check_publication_status(response):
    try:
        current_status = response.json().get('layman_metadata', {}).get('publication_status')
    except json.JSONDecodeError as exc:
        print(f'response={response.text}')
        raise exc
    return current_status in {'COMPLETE', 'INCOMPLETE'}


def wait_for_publication_status(workspace, publication_type, publication, *, check_response_fn=None, headers=None,
                                raise_if_not_complete=True):
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]
    with app.app_context():
        url = url_for(publication_type_def.get_workspace_publication_url,
                      workspace=workspace,
                      **{publication_type_def.url_param_name: publication})
    check_response_fn = check_response_fn or check_publication_status
    response = wait_for_rest(url, 60, 0.5, check_response=check_response_fn, headers=headers)
    if raise_if_not_complete:
        raise_if_not_complete_status(response)


def patch_after_feature_change(workspace, publ_type, name):
    queue = LAYMAN_CELERY_QUEUE
    with app.app_context():
        layman_util.patch_after_feature_change(workspace, publ_type, name, queue=queue)


def get_workspace_map_file(publication_type, workspace, name, headers=None, actor_name=None):
    headers = headers or {}
    assert publication_type == MAP_TYPE
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]
    if actor_name:
        assert TOKEN_HEADER not in headers

    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))

    with app.app_context():
        r_url = url_for('rest_workspace_map_file.get', **{publication_type_def.url_param_name: name}, workspace=workspace)
    response = requests.get(r_url, headers=headers, timeout=HTTP_TIMEOUT)
    raise_layman_error(response)
    return response.json()


def get_workspace_publication_thumbnail(publication_type, workspace, name, *, actor_name=None):
    headers = {}
    publication_type_def = PUBLICATION_TYPES_DEF[publication_type]
    if actor_name:
        assert TOKEN_HEADER not in headers

    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))

    with app.app_context():
        r_url = url_for(publication_type_def.get_workspace_publication_thumbnail_url, **{publication_type_def.url_param_name: name}, workspace=workspace)
    response = requests.get(r_url, headers=headers, timeout=HTTP_TIMEOUT)
    raise_layman_error(response)
    return response.content


def get_users(*, headers=None):
    headers = headers or {}
    with app.app_context():
        r_url = url_for('rest_users.get')
    response = requests.get(r_url, headers=headers, timeout=HTTP_TIMEOUT)
    response.raise_for_status()
    return response.json()


def delete_user(username, *, actor_name):
    with app.app_context():
        url = url_for('rest_user.delete', username=username)
    headers = {}
    if actor_name:
        assert TOKEN_HEADER not in headers
    if actor_name and actor_name != settings.ANONYM_USER:
        headers.update(get_authz_headers(actor_name))
    response = requests.delete(url, headers=headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    return response
