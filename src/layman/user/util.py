from flask import g
from layman import LaymanError
from layman.authn import get_open_id_claims, get_iss_id, get_sub
from layman.util import slugify, to_safe_names, check_username, get_usernames, ensure_user_workspace, delete_user_workspace
from layman.authn import redis as authn_redis, filesystem as authn_filesystem


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


def reserve_username(username, adjust=False):
    # todo accept also email (or general claims) and save it with reservation
    if 'username' in g.user:
        raise LaymanError(34, {'username': g.user['username']})
    if adjust is not True:
        check_username(username)
        usernames = get_usernames()
        if username in usernames:
            raise LaymanError(35)
        try:
            ensure_user_workspace(username)
            _save_reservation(username)
        except LaymanError as e:
            delete_user_workspace(username)
            raise e
        return
    claims = get_open_id_claims()
    suggestions = [username] + get_username_suggestions_from_claims(claims)
    suggestions = [
        slugify(s) for s in suggestions if s is not None and len(s) > 0
    ]
    suggestions = to_safe_names(suggestions, 'user')
    usernames = get_usernames()
    username = None
    while True:
        idx = 0
        for suggestion in suggestions:
            if idx > 0:
                suggestion = f"{suggestion}{idx}"
            try:
                check_username(suggestion)
            except LaymanError as e:
                if not (e.code == 2 or e.code == 35):
                    raise e
            if suggestion in usernames:
                continue
            try:
                ensure_user_workspace(suggestion)
                username = suggestion
                _save_reservation(username)
                break
            except LaymanError:
                delete_user_workspace(suggestion)
        if username is not None:
            break
        idx += 1


def _save_reservation(username):
    iss_id = get_iss_id()
    sub = get_sub()
    authn_redis.save_username_reservation(username, iss_id, sub)
    authn_filesystem.save_username_reservation(username, iss_id, sub)
    g.user['username'] = username


def get_username_suggestions_from_claims(claims):
    keys = [
        'preferred_username',
        'nickname',
        'name',
        'email',
        'sub',
    ]
    result = [
        claims.get(k, None) for k in keys
    ]
    return result

