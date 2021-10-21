from layman import app, util as layman_util, settings
from test_tools import process_client, util as test_util, assert_util
from ... import util


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
                assert_util.assert_same_values_for_keys(expected=info[key],
                                                        tested=value,
                                                        missing_key_is_ok=True,
                                                        path=f'[{source}]',
                                                        )


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


def mandatory_keys_in_primary_db_schema_of_actor(workspace, publ_type, name, actor, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'actor_name': actor, 'keys': []})
    assert {'name', 'title', 'access_rights', 'uuid', }.issubset(set(pub_info)), pub_info


def other_keys_not_in_primary_db_schema_of_actor(workspace, publ_type, name, actor, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'actor_name': actor, 'keys': []})
    assert all(item not in pub_info for item in {'metadata', 'file', }), pub_info


def mandatory_keys_in_all_sources_of_actor(workspace, publ_type, name, actor, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'actor_name': actor})
    assert {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file', }.issubset(set(pub_info)), pub_info


def thumbnail_equals(workspace, publ_type, name, exp_thumbnail, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['thumbnail']})

    diffs = test_util.compare_images(exp_thumbnail, pub_info['_thumbnail']['path'])
    assert diffs < 500


def correct_values_in_detail(workspace, publ_type, name, exp_publication_detail):
    publ_type_dir = util.get_directory_name_from_publ_type(publ_type)
    expected_detail = {
        'name': name,
        'title': name,
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
    expected_detail = util.recursive_dict_update(expected_detail, exp_publication_detail)
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name)
    assert_util.assert_same_values_for_keys(expected=expected_detail,
                                            tested=pub_info,
                                            )


def does_not_exist(workspace, publ_type, name, ):
    with app.app_context():
        pub_info = layman_util.get_publication_info(workspace, publ_type, name)
    assert not pub_info, pub_info
