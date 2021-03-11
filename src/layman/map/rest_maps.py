from flask import Blueprint, jsonify, g
from flask import current_app as app

from layman.util import url_for
from layman import util as layman_util
from . import MAP_TYPE, MAP_REST_PATH_NAME
from layman.authn import authenticate
from layman.authz import authorize_publications_decorator

bp = Blueprint('rest_maps', __name__)


@bp.before_request
@authenticate
@authorize_publications_decorator
def before_request():
    pass


@bp.route(f"/{MAP_REST_PATH_NAME}", methods=['GET'])
def get():
    app.logger.info(f"GET Maps, user={g.user}")

    user = g.user.get('username') if g.user else None
    map_infos_whole = layman_util.get_publication_infos(publ_type=MAP_TYPE, context={'actor_name': user,
                                                                                     'access_type': 'read',
                                                                                     })

    infos = [
        {
            'name': name,
            'workspace': workspace,
            'title': info.get("title", None),
            'url': url_for('rest_workspace_map.get', mapname=name, username=workspace),
            'uuid': info["uuid"],
            'access_rights': info['access_rights'],
        }
        for (workspace, _, name), info in map_infos_whole.items()
    ]
    return jsonify(infos), 200
