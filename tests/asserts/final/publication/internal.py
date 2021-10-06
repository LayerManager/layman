from layman import app, util as layman_util, settings
from test_tools import process_client
from ... import util as assert_util


def source_has_its_key_or_it_is_empty(workspace, publ_type, name):
    with app.app_context():
        all_items = layman_util.get_publication_types()[publ_type]['internal_sources'].values()
        for source_def in all_items:
            for key in source_def.info_items:
                context = {'keys': [key]}
                info = layman_util.get_publication_info(workspace, publ_type, name, context)
                assert key in info or not info, info


def source_internal_keys_are_subset_of_source_sibling_keys(workspace, publ_type, name):
    with app.app_context():
        all_items = layman_util.get_publication_types()[publ_type]['internal_sources'].values()
        for source_def in all_items:
            for key in source_def.info_items:
                context = {'keys': [key]}
                info = layman_util.get_publication_info(workspace, publ_type, name, context)
                all_sibling_keys = set(sibling_key for item_list in all_items for sibling_key in item_list.info_items
                                       if key in item_list.info_items)
                internal_keys = [key[1:] for key in info if key.startswith('_')]
                assert set(internal_keys) <= all_sibling_keys, \
                    f'internal_keys={set(internal_keys)}, all_sibling_keys={all_sibling_keys}, key={key}, info={info}'


def same_value_of_key_in_all_sources(workspace, publ_type, name):
    with app.app_context():
        sources = layman_util.get_internal_sources(publ_type)
        info = layman_util.get_publication_info(workspace, publ_type, name)

    info_method = {
        process_client.LAYER_TYPE: 'get_layer_info',
        process_client.MAP_TYPE: 'get_map_info',
    }[publ_type]
    with app.app_context():
        partial_infos = layman_util.call_modules_fn(sources, info_method, [workspace, name])

    for source, source_info in partial_infos.items():
        for key, value in source_info.items():
            if key in info:
                assert assert_util.same_infos(info[key], value), f'{source}: key={key}, info={info[key]}, source={value}, ' \
                                                                 f'all={[(lsource, lsource_info[key]) for lsource, lsource_info in partial_infos.items() if key in lsource_info]}'


def mandatory_keys_in_all_sources(workspace, publ_type, name):
    # Items
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name)
    assert {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file', }.issubset(set(pub_info)), pub_info


def metadata_key_sources_do_not_contain_other_keys(workspace, publ_type, name):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['metadata']})
    assert {'metadata', }.issubset(set(pub_info)), pub_info
    assert all(item not in pub_info for item in {'name', 'title', 'access_rights', 'uuid', 'file', }), pub_info


def thumbnail_key_sources_do_not_contain_other_keys(workspace, publ_type, name):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['thumbnail']})
    assert {'thumbnail', }.issubset(set(pub_info)), pub_info
    assert all(item not in pub_info for item in {'name', 'title', 'access_rights', 'uuid', 'file', 'metadata', }), pub_info


def mandatory_keys_in_primary_db_schema_of_first_reader(workspace, publ_type, name, actor, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'actor_name': actor, 'keys': []})
    assert {'name', 'title', 'access_rights', 'uuid', }.issubset(set(pub_info)), pub_info


def other_keys_not_in_primary_db_schema_of_first_reader(workspace, publ_type, name, actor, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'actor_name': actor, 'keys': []})
    assert all(item not in pub_info for item in {'metadata', 'file', }), pub_info


def mandatory_keys_in_all_sources_of_first_reader(workspace, publ_type, name, actor, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'actor_name': actor})
    assert {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file', }.issubset(set(pub_info)), pub_info


def correct_values_in_detail(workspace, publ_type, name, exp_publication_detail):
    publ_type_dir = publ_type.split('.')[1] + 's'
    expected_detail = {
        'name': name,
        'type': publ_type,
        'thumbnail': {
            'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type_dir}/{name}/thumbnail',
            'path': f'{publ_type_dir}/{name}/thumbnail/{name}.png'
        },
        'metadata': {
            'comparison_url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type_dir}/{name}/metadata-comparison'
        },
    }
    if publ_type == process_client.LAYER_TYPE:
        expected_detail.update({
            'db_table': {'name': name},
            'style': {
                'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type_dir}/{name}/style',
            },
            'wms': {'url': f'{settings.LAYMAN_GS_PROXY_BASE_URL}{workspace}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}/ows'},
            '_wms': {'url': f'{settings.LAYMAN_GS_URL}{workspace}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}/ows',
                     'workspace': f'{workspace}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}'},
        })
    for key, item in exp_publication_detail.items():
        if isinstance(item, dict) and isinstance(expected_detail.get(key), dict):
            expected_detail[key].update(item)
        else:
            expected_detail[key] = item
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name)
    assert assert_util.same_infos(expected_detail, pub_info), f'expected_detail={expected_detail}\npub_info={pub_info}\n' \
                                                              f'exp_publication_detail={exp_publication_detail}'


def does_not_exist(workspace, publ_type, name, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name)
    assert not pub_info, pub_info
