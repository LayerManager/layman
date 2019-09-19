from layman.authn import get_open_id_claims


def get_user_profile(user_obj):
    if user_obj is None:
        result = {
            'authenticated': False,
        }
    else:
        username = user_obj.get('name', None)
        result = {
            'authenticated': True,
            'name': username,
        }
    result = {k: v for k, v in result.items() if v is not None}
    claims = get_open_id_claims().copy()
    claims.pop('updated_at', None)
    result['claims'] = claims
    return result