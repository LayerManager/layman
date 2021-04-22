from flask import g
from layman import LaymanError, authn
from layman.authn import get_open_id_claims, get_iss_id, get_sub, is_user_with_name
from layman.util import slugify, to_safe_names, check_username, get_workspaces, ensure_whole_user, delete_whole_user
from layman.authn import redis as authn_redis, filesystem as authn_filesystem, prime_db_schema as authn_prime_db_schema


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
    result['claims'] = claims
    if result['claims'].get('preferred_username'):
        result['claims']['screen_name'] = result['claims']['preferred_username']
    return result


def reserve_username(username, adjust=False):
    current_username = authn.get_authn_username()
    if is_user_with_name(current_username):
        raise LaymanError(34, {'username': current_username})
    if adjust is not True:
        check_username(username)
        usernames = get_workspaces()
        if username in usernames:
            raise LaymanError(35)
        try:
            ensure_whole_user(username)
            claims = get_open_id_claims()
            _save_reservation(username, claims)
        except LaymanError as e:
            delete_whole_user(username)
            raise e
        return
    claims = get_open_id_claims()
    suggestions = [username] + get_username_suggestions_from_claims(claims)
    suggestions = [
        slugify(s) for s in suggestions if s is not None and len(s) > 0
    ]
    suggestions = to_safe_names(suggestions, 'user')
    usernames = get_workspaces()
    username = None
    idx = 0
    while True:
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
                ensure_whole_user(suggestion)
                username = suggestion
                _save_reservation(username, claims)
                break
            except LaymanError:
                delete_whole_user(suggestion)
        if username is not None:
            break
        idx += 1


def _save_reservation(username, claims):
    iss_id = get_iss_id()
    sub = get_sub()
    authn_redis.save_username_reservation(username, iss_id, sub)
    authn_filesystem.save_username_reservation(username, iss_id, sub, claims)
    authn_prime_db_schema.save_username_reservation(username, iss_id, sub, claims)
    g.user['username'] = username


def get_username_suggestions_from_claims(claims):
    keys = [
        'nickname',
        'preferred_username',
        'name',
    ]
    result = [
        claims.get(k, None) for k in keys
    ]
    email = claims.get('email', None)
    if email is not None:
        result.append(email.split('@')[0])
    return result
