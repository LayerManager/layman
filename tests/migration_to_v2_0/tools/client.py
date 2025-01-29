from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import time
from contextlib import ExitStack
from dataclasses import dataclass

import requests
import layman_settings as settings
from .http import LaymanError
from .util import compress_files

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


@dataclass(frozen=True)
class PublicationTypeDef:
    url_param_name: str
    get_publications_url: str
    post_workspace_publication_url: str | None
    patch_workspace_publication_url: str | None
    get_workspace_publications_url: str | None
    get_workspace_publication_url: str | None
    get_workspace_publication_thumbnail_url: str | None
    delete_workspace_publication_url: str | None
    delete_workspace_publications_url: str | None
    keys_to_check: list | None
    source_path: str | None
    get_workspace_metadata_comparison_url: str | None
    url_path_name: str | None
    post_workspace_publication_chunk: str | None


PUBLICATION_TYPES_DEF = {
    MAP_TYPE: PublicationTypeDef(url_param_name='mapname',
                                 get_publications_url='rest_maps.get',
                                 post_workspace_publication_url='rest_workspace_maps.post',
                                 patch_workspace_publication_url='rest_workspace_map.patch',
                                 get_workspace_publications_url='rest_workspace_maps.get',
                                 get_workspace_publication_url='rest_workspace_map.get',
                                 get_workspace_publication_thumbnail_url='rest_workspace_map_thumbnail.get',
                                 delete_workspace_publication_url='rest_workspace_map.delete_map',
                                 delete_workspace_publications_url='rest_workspace_maps.delete',
                                 keys_to_check=map_keys_to_check,
                                 source_path='sample/layman.map/small_map.json',
                                 get_workspace_metadata_comparison_url='rest_workspace_map_metadata_comparison.get',
                                 url_path_name='maps',
                                 post_workspace_publication_chunk=None,
                                 ),
    LAYER_TYPE: PublicationTypeDef(url_param_name='layername',
                                   get_publications_url='rest_layers.get',
                                   post_workspace_publication_url='rest_workspace_layers.post',
                                   patch_workspace_publication_url='rest_workspace_layer.patch',
                                   get_workspace_publications_url='rest_workspace_layers.get',
                                   get_workspace_publication_url='rest_workspace_layer.get',
                                   get_workspace_publication_thumbnail_url='rest_workspace_layer_thumbnail.get',
                                   delete_workspace_publication_url='rest_workspace_layer.delete_layer',
                                   delete_workspace_publications_url='rest_workspace_layers.delete',
                                   keys_to_check=layer_keys_to_check,
                                   source_path='sample/layman.layer/small_layer.geojson',
                                   get_workspace_metadata_comparison_url='rest_workspace_layer_metadata_comparison.get',
                                   url_path_name='layers',
                                   post_workspace_publication_chunk='rest_workspace_layer_chunk.post',
                                   ),
    None: PublicationTypeDef(url_param_name='publicationname',
                             get_publications_url='rest_publications.get',
                             post_workspace_publication_url=None,
                             patch_workspace_publication_url=None,
                             get_workspace_publications_url=None,
                             get_workspace_publication_url=None,
                             get_workspace_publication_thumbnail_url=None,
                             delete_workspace_publication_url=None,
                             delete_workspace_publications_url=None,
                             keys_to_check=None,
                             source_path=None,
                             get_workspace_metadata_comparison_url=None,
                             url_path_name=None,
                             post_workspace_publication_chunk=None,
                             ),
}


def get_authz_headers(username):
    return {f'{TOKEN_HEADER}': f'Bearer {username}'}


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


def check_publication_status(response):
    try:
        current_status = response.json().get('layman_metadata', {}).get('publication_status')
    except json.JSONDecodeError as exc:
        print(f'response={response.text}')
        raise exc
    return current_status in {'COMPLETE', 'INCOMPLETE'}


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


class RestClient:

    def __init__(self, base_url: str):
        self.base_url: str = base_url

    def reserve_username(self, username, headers=None, *, actor_name=None):
        headers = headers or {}
        if actor_name:
            assert TOKEN_HEADER not in headers

        if actor_name and actor_name != settings.ANONYM_USER:
            headers.update(get_authz_headers(actor_name))
        r_url = f"{self.base_url}/rest/current-user"
        data = {
            'username': username,
        }
        response = requests.patch(r_url, headers=headers, data=data, timeout=HTTP_TIMEOUT)
        raise_layman_error(response)
        claimed_username = response.json()['username']
        assert claimed_username == username

    def post_workspace_publication(self,
                                   publication_type,
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
                                   # map_layers=None,  # not yet supported
                                   native_extent=None,
                                   overview_resampling=None,
                                   do_not_upload_chunks=False,
                                   time_regex=None,
                                   time_regex_format=None,
                                   do_not_post_name=False,
                                   ):
        map_layers = None  # if someone needs it, make it an argument and implement functionality

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

        r_url = f"{self.base_url}/rest/workspaces/{workspace}/{publication_type_def.url_path_name}"

        temp_dir = None
        if compress:
            temp_dir = tempfile.mkdtemp(prefix="layman_zip_")
            zip_file = compress_files(file_paths, compress_settings=compress_settings, output_dir=temp_dir)
            file_paths = [zip_file]

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
            self.upload_file_chunks(publication_type,
                                    workspace,
                                    name,
                                    file_paths, )

        if not do_not_upload_chunks:
            self.wait_for_publication_status(workspace, publication_type, name, check_response_fn=check_response_fn,
                                             headers=headers, raise_if_not_complete=raise_if_not_complete)
        if temp_dir:
            shutil.rmtree(temp_dir)
        return response.json()[0]

    def upload_file_chunks(self,
                           publication_type,
                           workspace,
                           name,
                           file_paths,
                           ):
        publication_type_def = PUBLICATION_TYPES_DEF[publication_type]
        time.sleep(0.5)
        chunk_url = f"{self.base_url}/rest/workspaces/{workspace}/{publication_type_def.url_path_name}/{name}/chunk"

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

    def wait_for_publication_status(self, workspace, publication_type, publication, *, check_response_fn=None,
                                    headers=None, raise_if_not_complete=True):
        publication_type_def = PUBLICATION_TYPES_DEF[publication_type]
        r_url = f"{self.base_url}/rest/workspaces/{workspace}/{publication_type_def.url_path_name}/{publication}"
        check_response_fn = check_response_fn or check_publication_status
        response = wait_for_rest(r_url, 60, 0.5, check_response=check_response_fn, headers=headers)
        if raise_if_not_complete:
            raise_if_not_complete_status(response)
