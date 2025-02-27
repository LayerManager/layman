from flask import g
from layman import LaymanError, authn
from layman.authn import get_open_id_claims, get_iss_id, get_sub, is_user_with_name
from layman.util import slugify, to_safe_names, check_workspace_name, get_workspaces, ensure_whole_user, delete_whole_user
from layman.authn import redis as authn_redis, prime_db_schema as authn_prime_db_schema
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from layman.layer.util import delete_layer, patch_layer
from layman.map.util import delete_map, patch_map
from layman.common.prime_db_schema.publications import get_publication_infos_with_metainfo


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
    if not adjust:
        check_workspace_name(username)
        workspaces = get_workspaces()
        if username in workspaces:
            raise LaymanError(35)
        try:
            ensure_whole_user(username)
            claims = get_open_id_claims()
            _save_reservation(username, claims)
        except LaymanError as exc:
            delete_whole_user(username)
            raise exc
        return
    claims = get_open_id_claims()
    suggestions = [username] + get_username_suggestions_from_claims(claims)
    suggestions = [
        slugify(s) for s in suggestions if s is not None and len(s) > 0
    ]
    suggestions = to_safe_names(suggestions, 'user')
    workspaces = get_workspaces()
    username = None
    idx = 0
    while True:
        for suggestion in suggestions:
            if idx > 0:
                suggestion = f"{suggestion}{idx}"
            try:
                check_workspace_name(suggestion)
            except LaymanError as exc:
                if exc.code not in (2, 35, 41, 45):
                    raise exc
                continue
            if suggestion in workspaces:
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


def delete_user(username=None):
    authn_redis.delete_user(username)
    delete_whole_user(username)

def delete_user_public_publications(username):
    result = get_publication_infos_with_metainfo()
    for key, pubinfo in result['items'].items():
        workspace, publication_type, publication_name = key
        is_public = pubinfo.get('_is_public_workspace')
        access_rights = pubinfo.get('access_rights')
        is_only_rw = (
                set(access_rights.get('read', [])) == {username} and
                set(access_rights.get('write', [])) == {username}
        )
        publication_name = pubinfo['name']

        if is_public and is_only_rw:
            if publication_type == LAYER_TYPE:
                delete_layer(workspace, publication_name)
            if publication_type == MAP_TYPE:
                delete_map(workspace, publication_name)

        elif is_public and not is_only_rw:
            new_read = [u for u in access_rights.get('read', []) if u != username]
            new_write = [u for u in access_rights.get('write', []) if u != username]
            kwargs = {
                "access_rights": {
                    "read": new_read,
                    "write": new_write
                },
                "actor_name": new_write[0],
                "external_table_uri": pubinfo.get('external_table_uri'),
                "geodata_type": pubinfo.get('geodata_type'),
                "title": pubinfo.get('title'),
                "description": pubinfo.get('description'),
                "original_data_source": pubinfo.get('original_data_source')
            }
            if publication_type == LAYER_TYPE:
                patch_layer(workspace, publication_name, kwargs, None, None, True)
            if publication_type ==  MAP_TYPE:
                patch_map(workspace, publication_name, kwargs, None, True)
