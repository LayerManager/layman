from layman import settings
from .. import util as assert_util


def valid_post(workspace, publ_type, name, response, expected=None):
    expected = expected or dict()
    publ_type_dir = assert_util.get_directory_name_from_publ_type(publ_type)
    exp_response = {
        'name': name,
        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/{publ_type_dir}/{name}'
    }
    exp_response = assert_util.recursive_dict_update(exp_response, expected)
    assert assert_util.same_value_for_keys(expected=exp_response,
                                           tested=response), f'exp_response={exp_response}\nresponse={response}\nexpected={expected}'
