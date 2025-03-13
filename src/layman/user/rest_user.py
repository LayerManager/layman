from flask import current_app as app, g, Blueprint, jsonify, request
from layman.authn import authenticate, get_authn_username
from layman.authz import is_allowed_to_delete_user
from layman import util as layman_util, LaymanError
from layman.common.prime_db_schema.users import get_user_infos
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from .util import delete_user, delete_user_public_publications


bp = Blueprint('rest_user', __name__)


@bp.before_request
@authenticate
def before_request():
    pass


@bp.route('/<username>', methods=['DELETE'])
def delete(username):
    app.logger.info(f"DELETE User request for username={username} by user={g.user}")
    if username not in get_user_infos(username):
        app.logger.warning(f"User {username} does not exist.")
        raise LaymanError(57, {'message': f'User {username} was not found.'})
    actor_name = get_authn_username()
    if not is_allowed_to_delete_user(username=username, actor_name=actor_name):
        app.logger.info(f"User {actor_name} is not authorized to delete {username}.")
        raise LaymanError(30, {'message': f'User {actor_name} is not authorized to delete {username}.'})
    x_forwarded_items = layman_util.get_x_forwarded_items(request.headers)
    delete_user_public_publications(username)

    layman_util.delete_publications(
        username,
        LAYER_TYPE,
        request.method,
        'rest_workspace_layer.get',
        'layername',
        x_forwarded_items=x_forwarded_items,
        actor_name=username,
    )
    layman_util.delete_publications(
        username,
        MAP_TYPE,
        request.method,
        'rest_workspace_map.get',
        'mapname',
        x_forwarded_items=x_forwarded_items,
        actor_name=username,
    )
    delete_user(username)
    return jsonify({
        'username': username
    }), 200
