from layman.authn.util import get_authn_module_by_iss_id
from layman.common.prime_db_schema import ensure_whole_user
from layman.common.prime_db_schema import users


def save_username_reservation(username, iss_id, sub, claims):
    userinfo = {"issuer_id": iss_id,
                "sub": sub,
                "claims": claims,
                }
    ensure_whole_user(username, userinfo)


def get_authn_info(username):
    user_info = users.get_user_infos(username).get(username)
    if user_info:
        iss_id = user_info['issuer_id']
        authn_module = get_authn_module_by_iss_id(iss_id)
        iss = authn_module.get_iss() if authn_module else None
        result = {
            'iss_id': iss_id,
            'sub': user_info['sub'],
            'claims': {
                'iss': iss,
                'sub': user_info['sub'],
                'email': user_info['email'],
                'name': user_info['name'],
                'given_name': user_info['given_name'],
                'family_name': user_info['family_name'],
                'middle_name': user_info['middle_name'],
                'preferred_username': user_info['preferred_username'],
            },
        }
    else:
        result = {}
    return result
