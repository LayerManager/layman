from flask import Blueprint, jsonify, g
from flask import current_app as app

from layman.util import url_for
from layman import util as layman_util, settings
from . import LAYER_TYPE, LAYER_REST_PATH_NAME
from layman.authn import authenticate

bp = Blueprint('rest_layers', __name__)


@bp.before_request
@authenticate
def before_request():
    pass


@bp.route(f"/{LAYER_REST_PATH_NAME}", methods=['GET'])
def get():
    app.logger.info(f"GET Layers, user={g.user}")

    user = g.user.get('username') if g.user else settings.ANONYM_USER
    layer_infos_whole = layman_util.get_publication_infos(publ_type=LAYER_TYPE, context={'actor_name': user,
                                                                                         'access_type': 'read',
                                                                                         })

    infos = [
        {
            'name': name,
            'workspace': workspace,
            'title': info.get("title", None),
            'url': url_for('rest_workspace_layer.get', layername=name, username=workspace),
            'uuid': info["uuid"],
            'access_rights': info['access_rights'],
        }
        for (workspace, _, name), info in layer_infos_whole.items()
    ]
    return jsonify(infos), 200
