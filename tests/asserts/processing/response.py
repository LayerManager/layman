from layman import settings
from test_tools import assert_util
from .. import util


def valid_post(workspace, publ_type, name, response, expected=None):
    expected = expected or {}
    publ_type_dir = util.get_directory_name_from_publ_type(publ_type)
    exp_response = {
        'name': name,
        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type_dir}/{name}'
    }
    exp_response = util.recursive_dict_update(exp_response, expected)
    assert_util.assert_same_values_for_keys(expected=exp_response,
                                            tested=response,
                                            )
