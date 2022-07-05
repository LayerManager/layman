from celery import states
from layman import app
from layman.layer import LAYER_TYPE
from test_tools import process_client, util as test_util


def is_in_rest_multi(workspace, publ_type, name, headers):
    infos = process_client.get_workspace_publications(publ_type, workspace, headers=headers)

    publication_infos = [info for info in infos if info['name'] == name]
    assert len(publication_infos) == 1, f'publication_infos={publication_infos}'


def correct_url_in_rest_multi(workspace, publ_type, name, headers):
    infos = process_client.get_workspace_publications(publ_type, workspace, headers=headers)
    publication_infos = [info for info in infos if info['name'] == name]
    info = next(iter(publication_infos))
    get_workspace_publication_url = process_client.PUBLICATION_TYPES_DEF[publ_type].get_workspace_publication_url
    param_name = process_client.PUBLICATION_TYPES_DEF[publ_type].url_param_name
    with app.app_context():
        expected_url = test_util.url_for(get_workspace_publication_url, workspace=workspace, **{param_name: name},
                                         internal=False)
        assert info['url'] == expected_url, f'publication_infos={publication_infos}, expected_url={expected_url}'


def correct_file_type_in_rest_multi(workspace, publ_type, name, headers, exp_file_type):
    infos = process_client.get_workspace_publications(publ_type, workspace, headers=headers)
    publication_infos = [info for info in infos if info['name'] == name]
    info = next(iter(publication_infos))
    if publ_type == LAYER_TYPE:
        assert info['file']['file_type'] == exp_file_type
    else:
        assert 'file' not in info


def is_complete_in_rest(rest_publication_detail):
    assert 'layman_metadata' in rest_publication_detail, f'rest_publication_detail={rest_publication_detail}'
    assert rest_publication_detail['layman_metadata']['publication_status'] == 'COMPLETE', f'rest_publication_detail={rest_publication_detail}'


def mandatory_keys_in_rest(rest_publication_detail):
    assert {'name', 'title', 'access_rights', 'uuid', 'metadata', 'file'}.issubset(set(rest_publication_detail)), rest_publication_detail


def async_error_in_info_key(rest_publication_detail, info_key, expected):
    assert rest_publication_detail['layman_metadata']['publication_status'] == 'INCOMPLETE'
    assert rest_publication_detail[info_key]['status'] == states.FAILURE
    test_util.assert_async_error(expected,
                                 rest_publication_detail[info_key]['error'])
