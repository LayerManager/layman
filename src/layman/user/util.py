from flask import g
from layman import LaymanError, authn
from layman.authn import get_open_id_claims, get_iss_id, get_sub, is_user_with_name
from layman.publication_class import Publication
from layman.util import slugify, to_safe_names, check_workspace_name, get_workspaces, ensure_whole_user, delete_whole_user, get_publication_infos, patch_publication, delete_workspace_publication
from layman.authn import redis as authn_redis, prime_db_schema as authn_prime_db_schema
from layman.layer import LAYER_TYPE, util as layer_util
from layman.map import util as map_util
from layman.authz import is_user
from layman_settings import RIGHTS_EVERYONE_ROLE


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


def check_if_is_only_rw(access_rights, username):
    read_set = set(access_rights['read'])
    write_set = set(access_rights['write'])
    if RIGHTS_EVERYONE_ROLE in read_set or RIGHTS_EVERYONE_ROLE in write_set:
        return False
    read_users = {u for u in read_set if is_user(u)}
    write_users = {u for u in write_set if is_user(u)}
    return (read_users == {username}) and (write_users == {username})


def delete_user_public_publications(username):
    def has_only_roles_without_everyone(user_list):
        return all(not is_user(u) and u != RIGHTS_EVERYONE_ROLE for u in user_list)

    skipped_publications = []
    publications_to_be_deleted = []
    publications_to_be_patched = []
    result = get_publication_infos(
        context={
            'actor_name': username,
            'access_type': 'read',
        },
    )

    for (workspace, publication_type, publication_name), pubinfo in result.items():
        is_public = pubinfo['_is_public_workspace']
        access_rights = pubinfo['access_rights']
        geodata_type = pubinfo['geodata_type']
        is_only_rw = check_if_is_only_rw(access_rights, username)
        publication_name = pubinfo['name']
        uuid = pubinfo["uuid"]

        if is_public and is_only_rw:
            publications_to_be_deleted.append((workspace, publication_type, publication_name))
        elif is_public and not is_only_rw:
            new_read = [u for u in access_rights['read'] if u != username]
            new_write = [u for u in access_rights['write'] if u != username]
            if (
                    username in access_rights['read']
                    and has_only_roles_without_everyone(new_write)
            ):
                skipped_publications.append({
                    "workspace": workspace,
                    "type": publication_type,
                    "name": publication_name,
                    "uuid": uuid,
                })
                continue

            publications_to_be_patched.append(
                (workspace, publication_name, publication_type, pubinfo, new_read, new_write, geodata_type)
            )
    if skipped_publications:
        raise LaymanError(58, {
            'message': f"User {username} cannot be removed from some publications because other users have read rights.",
            'username': username,
            'unable_to_delete_publications': skipped_publications,
        })

    for (workspace, publication_name, publication_type, pubinfo, new_read, new_write, geodata_type) in publications_to_be_patched:
        kwargs = {
            "access_rights": {
                "read": new_read,
                "write": new_write
            },
            "uuid": pubinfo["uuid"],
            "actor_name": username,
            "external_table_uri": pubinfo.get('external_table_uri'),
            "geodata_type": geodata_type,
            "title": pubinfo.get('title'),
            "description": pubinfo.get('description'),
            "original_data_source": pubinfo.get('original_data_source'),
            "is_part_of_user_delete": True,
        }

        old_publication = Publication.create(publ_tuple=(workspace, publication_type, publication_name))
        new_publication = old_publication.clone(access_rights=kwargs['access_rights'])
        patch_publication(
            new_publication,
            layer_util.patch_layer if publication_type == LAYER_TYPE else map_util.patch_map,
            layer_util.is_layer_chain_ready if publication_type == LAYER_TYPE else map_util.is_map_chain_ready,
            kwargs,
            {
                "stop_sync_at": None,
                "start_async_at": None,
                "only_sync": True
            } if publication_type == LAYER_TYPE else {
                "start_at": None,
                "only_sync": True
            }
        )

    for workspace, publication_type, publication_name in publications_to_be_deleted:
        delete_workspace_publication(workspace=workspace, publication_type=publication_type, publication_name=publication_name, method='delete')

    return skipped_publications
