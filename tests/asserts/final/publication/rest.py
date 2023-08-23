import copy

from celery import states
from layman import settings
from test_tools import process_client, util as test_util

PROXY_PREFIX = '/layman-proxy'


def is_complete_in_rest(rest_publication_detail):
    assert 'layman_metadata' in rest_publication_detail, f'rest_publication_detail={rest_publication_detail}'
    assert rest_publication_detail['layman_metadata']['publication_status'] == 'COMPLETE', f'rest_publication_detail={rest_publication_detail}'


def mandatory_keys_in_rest(rest_publication_detail):
    assert {'name', 'title', 'access_rights', 'uuid', 'metadata', }.issubset(set(rest_publication_detail)), rest_publication_detail


def async_error_in_info_key(rest_publication_detail, info_key, expected):
    assert rest_publication_detail['layman_metadata']['publication_status'] == 'INCOMPLETE'
    assert rest_publication_detail[info_key]['status'] == states.FAILURE
    test_util.assert_async_error(expected,
                                 rest_publication_detail[info_key]['error'])


def same_values_in_detail_and_multi(workspace, publ_type, name, rest_publication_detail, headers, *, different_value_keys=None):
    different_value_keys = different_value_keys or []
    # keep only multi-endpoint keys
    expected_keys = ['workspace', 'name', 'title', 'uuid', 'url', 'updated_at', 'access_rights', 'bounding_box',
                     'native_crs', 'native_bounding_box']
    if publ_type == process_client.LAYER_TYPE:
        expected_keys += ['geodata_type', 'file']
    rest_detail = copy.deepcopy(rest_publication_detail)
    exp_info = {k: v for k, v in rest_detail.items() if k in expected_keys}

    # adjust deprecated `file` key
    if 'file' in exp_info:
        exp_info['file'] = {k: v for k, v in exp_info['file'].items() if k == 'file_type'}
    elif publ_type == process_client.LAYER_TYPE:
        exp_info['file'] = {
            'file_type': exp_info['geodata_type'],
        }

    # add other expected keys
    exp_info['workspace'] = workspace
    if publ_type == process_client.LAYER_TYPE:
        if any(k for k in ['wfs', 'wms', 'style'] if rest_detail.get(k, {}).get('status', None) in ['FAILURE', 'NOT_AVAILABLE']):
            wfs_wms_status = 'NOT_AVAILABLE'
        elif any(k for k in ['wfs', 'wms', 'style'] if rest_detail.get(k, {}).get('status', None) in ['PENDING', 'STARTED']):
            wfs_wms_status = 'PREPARING'
        else:
            wfs_wms_status = 'AVAILABLE'
        exp_info['wfs_wms_status'] = wfs_wms_status
    exp_info['publication_type'] = 'layer' if publ_type == process_client.LAYER_TYPE else 'map'

    for key in different_value_keys:
        exp_info.pop(key)

    multi_requests = [
        (process_client.get_publications, [publ_type], {'workspace': workspace, 'headers': headers}),
        (process_client.get_publications, [publ_type], {'headers': headers}),
        (process_client.get_publications, [None], {'headers': headers}),
    ]
    for rest_multi_method, args, kwargs in multi_requests:
        rest_multi_response_json = rest_multi_method(*args, **kwargs)
        rest_multi_infos = [info for info in rest_multi_response_json
                            if info['workspace'] == workspace and info['name'] == name and info['publication_type'] == publ_type.split('.')[1]]
        assert len(rest_multi_infos) == 1, f'rest_multi_infos={rest_multi_infos}'
        rest_multi_info = rest_multi_infos[0]

        for key in different_value_keys:
            rest_multi_info.pop(key)
        assert rest_multi_info == exp_info


def multi_url_with_x_forwarded_prefix(workspace, publ_type, name, headers, ):
    proxy_prefix = PROXY_PREFIX
    headers = {
        **(headers or {}),
        'X-Forwarded-Prefix': proxy_prefix,
    }
    short_publ_type = publ_type.split('.')[1]
    multi_requests = [
        (process_client.get_publications, [None], {'headers': headers}),
        (process_client.get_publications, [publ_type], {'headers': headers}),
        (process_client.get_publications, [publ_type], {'workspace': workspace, 'headers': headers}),
    ]
    for rest_multi_method, args, kwargs in multi_requests:
        rest_multi_response_json = rest_multi_method(*args, **kwargs)
        rest_multi_info = next(iter(info for info in rest_multi_response_json
                                    if info['workspace'] == workspace and info['name'] == name and info['publication_type']
                                    == short_publ_type))
        url = rest_multi_info['url']
        assert url == f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{workspace}/{short_publ_type}s/{name}'


def get_layer_with_x_forwarded_prefix(workspace, name, headers, ):
    proxy_prefix = PROXY_PREFIX
    headers = {
        **(headers or {}),
        'X-Forwarded-Prefix': proxy_prefix,
    }
    rest_layer_info = process_client.get_workspace_layer(workspace, name, headers=headers)
    assert rest_layer_info['url'] == f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{workspace}/layers/{name}'
    assert rest_layer_info['thumbnail']['url'] == f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{workspace}/layers/{name}/thumbnail'
    assert rest_layer_info['metadata']['comparison_url'] == f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{workspace}/layers/{name}/metadata-comparison'
    assert rest_layer_info['wms']['url'] == f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/geoserver/{workspace}_wms/ows'
    geodata_type = rest_layer_info['geodata_type']
    if geodata_type == settings.GEODATA_TYPE_VECTOR:
        assert rest_layer_info['wfs']['url'] == f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/geoserver/{workspace}/wfs'
    assert rest_layer_info['sld']['url'] == f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{workspace}/layers/{name}/style'
    assert rest_layer_info['style']['url'] == f'http://{settings.LAYMAN_PROXY_SERVER_NAME}{proxy_prefix}/rest/workspaces/{workspace}/layers/{name}/style'
