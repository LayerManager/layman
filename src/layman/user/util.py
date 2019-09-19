from layman.authn import get_open_id_claims


def get_user_profile(user_obj):
    if user_obj is None:
        result = {
            'authenticated': False,
        }
    else:
        username = user_obj.get('username', None)
        result = {
            'authenticated': True,
            'username': username,
        }
    result = {k: v for k, v in result.items() if v is not None}
    claims = get_open_id_claims().copy()
    claims.pop('updated_at', None)
    result['claims'] = claims
    return result