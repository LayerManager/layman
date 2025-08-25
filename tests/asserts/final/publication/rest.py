import copy

from celery import states

from layman import settings, app
from layman.layer.geoserver import GEOSERVER_WMS_WORKSPACE, GEOSERVER_WFS_WORKSPACE
from layman.util import XForwardedClass, get_publication_info
from test_tools import process_client, util as test_util, assert_util

X_FORWARDED_ITEMS = XForwardedClass(proto='https', host='abc.cz:3001', prefix='/layman-proxy')


def get_expected_urls_in_rest_response(workspace, publ_type, name, *, rest_method, x_forwarded_items=None, geodata_type=None, uuid=None):
    x_forwarded_items = x_forwarded_items or XForwardedClass()
    proxy_proto = x_forwarded_items.proto or settings.LAYMAN_PUBLIC_URL_SCHEME
    proxy_host = x_forwarded_items.host or settings.LAYMAN_PROXY_SERVER_NAME
    proxy_prefix = x_forwarded_items.prefix or ''
    assert rest_method in {'post', 'patch', 'get', 'delete', 'multi_delete'}
    publ_type_directory = f'{publ_type.split(".")[1]}s'
    if uuid is None and rest_method not in ['delete', 'multi_delete']:
        with app.app_context():
            uuid = get_publication_info(workspace=workspace, publ_type=publ_type, publ_name=name, context={'keys': ['uuid']})['uuid']
    result = {}
    if publ_type == "layman.map":
        result['url'] = f'{proxy_proto}://{proxy_host}{proxy_prefix}/rest/{publ_type_directory}/{uuid}'
    else:
        result[
            'url'] = f'{proxy_proto}://{proxy_host}{proxy_prefix}/rest/workspaces/{workspace}/{publ_type_directory}/{name}'

    if rest_method == 'get':
        if publ_type in [process_client.MAP_TYPE, process_client.LAYER_TYPE] and uuid:
            result['thumbnail'] = {
                'url': f'{proxy_proto}://{proxy_host}{proxy_prefix}/rest/{publ_type_directory}/{uuid}/thumbnail'
            }
        result['metadata'] = {
            'comparison_url': f'{proxy_proto}://{proxy_host}{proxy_prefix}/rest/workspaces/{workspace}/{publ_type_directory}/{name}/metadata-comparison',
        }
        if publ_type == process_client.LAYER_TYPE:
            result['wms'] = {
                'url': f'{proxy_proto}://{proxy_host}{proxy_prefix}/geoserver/{GEOSERVER_WMS_WORKSPACE}/ows',
            }
            result['style'] = {
                'url': f'{proxy_proto}://{proxy_host}{proxy_prefix}/rest/{publ_type_directory}/{uuid}/style',
            }
            if geodata_type == settings.GEODATA_TYPE_VECTOR:
                result['wfs'] = {
                    'url': f'{proxy_proto}://{proxy_host}{proxy_prefix}/geoserver/{GEOSERVER_WFS_WORKSPACE}/wfs'
                }
        else:
            result['file'] = {
                'url': f'{proxy_proto}://{proxy_host}{proxy_prefix}/rest/{publ_type_directory}/{uuid}/file',
            }

    return result


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
        expected_keys += ['geodata_type', 'used_in_maps']
    rest_detail = copy.deepcopy(rest_publication_detail)
    exp_info = {k: v for k, v in rest_detail.items() if k in expected_keys}

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
    proxy_items = X_FORWARDED_ITEMS
    headers = {
        **(headers or {}),
        **proxy_items.headers,
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
        if publ_type == 'layman.map':
            expected_url = f'{proxy_items.proto}://{proxy_items.host}{proxy_items.prefix}/rest/maps/{rest_multi_info["uuid"]}'
        else:
            expected_url = f'{proxy_items.proto}://{proxy_items.host}{proxy_items.prefix}/rest/workspaces/{workspace}/{short_publ_type}s/{name}'
        assert url == expected_url


def get_layer_with_x_forwarded_prefix(workspace, name, headers, ):
    proxy_items = X_FORWARDED_ITEMS
    headers = {
        **(headers or {}),
        **proxy_items.headers,
    }
    rest_layer_info = process_client.get_workspace_layer(workspace, name, headers=headers)
    geodata_type = rest_layer_info['geodata_type']

    exp_resp = get_expected_urls_in_rest_response(workspace, process_client.LAYER_TYPE, name,
                                                  rest_method='get',
                                                  x_forwarded_items=proxy_items,
                                                  geodata_type=geodata_type,
                                                  )
    assert_util.assert_same_values_for_keys(
        expected=exp_resp,
        tested=rest_layer_info,
    )


def get_map_with_x_forwarded_prefix(workspace, name, headers, ):
    proxy_items = X_FORWARDED_ITEMS
    headers = {
        **(headers or {}),
        **proxy_items.headers,
    }
    rest_map_info = process_client.get_workspace_map(workspace, name, headers=headers)
    exp_resp = get_expected_urls_in_rest_response(workspace, process_client.MAP_TYPE, name,
                                                  rest_method='get',
                                                  x_forwarded_items=proxy_items,
                                                  geodata_type=None,
                                                  )
    assert_util.assert_same_values_for_keys(
        expected=exp_resp,
        tested=rest_map_info,
    )
