from flask import jsonify
import re

from layman import settings, util as layman_util, LaymanError
from layman.common.prime_db_schema import util as prime_db_schema_util
from .util import PUBLICATION_NAME_ONLY_PATTERN
from . import get_publications_consts as consts


def _get_pub_type_pattern():
    publ_type_names = [publ_type['rest_path_name'] for publ_type in layman_util.get_publication_types().values()]
    publ_type_pattern = r"(?P<publication_type>" + "|".join(publ_type_names) + r")"
    return publ_type_pattern


def _get_workspace_multi_publication_path_pattern():
    workspace_pattern = r"(?P<workspace>" + layman_util.USERNAME_ONLY_PATTERN + r")"
    return f"^/rest/({settings.REST_WORKSPACES_PREFIX}/)?" + workspace_pattern + "/" + _get_pub_type_pattern()


_MULTI_PUBLICATION_PATH_PATTERN = None
_WORKSPACE_MULTI_PUBLICATION_PATH_PATTERN = None
_WORKSPACE_SINGLE_PUBLICATION_PATH_PATTERN = None
_URL_NAME_TO_PUBLICATION_TYPE = None


def get_multipublication_path_pattern():
    global _MULTI_PUBLICATION_PATH_PATTERN
    if _MULTI_PUBLICATION_PATH_PATTERN is None:
        _MULTI_PUBLICATION_PATH_PATTERN = re.compile(f"^/rest/" + _get_pub_type_pattern() + r"/?$")
    return _MULTI_PUBLICATION_PATH_PATTERN


def get_workspace_multipublication_path_pattern():
    global _WORKSPACE_MULTI_PUBLICATION_PATH_PATTERN
    if _WORKSPACE_MULTI_PUBLICATION_PATH_PATTERN is None:
        _WORKSPACE_MULTI_PUBLICATION_PATH_PATTERN = re.compile(_get_workspace_multi_publication_path_pattern() + r"/?$")
    return _WORKSPACE_MULTI_PUBLICATION_PATH_PATTERN


def get_singlepublication_path_pattern():
    global _WORKSPACE_SINGLE_PUBLICATION_PATH_PATTERN
    if _WORKSPACE_SINGLE_PUBLICATION_PATH_PATTERN is None:
        _WORKSPACE_SINGLE_PUBLICATION_PATH_PATTERN = re.compile(
            _get_workspace_multi_publication_path_pattern()
            + r"/(?P<publication_name>" + PUBLICATION_NAME_ONLY_PATTERN + r")(?:/.*)?$"
        )
    return _WORKSPACE_SINGLE_PUBLICATION_PATH_PATTERN


def get_url_name_to_publication_type():
    global _URL_NAME_TO_PUBLICATION_TYPE
    if _URL_NAME_TO_PUBLICATION_TYPE is None:
        _URL_NAME_TO_PUBLICATION_TYPE = {
            publ_type['rest_path_name']: publ_type
            for publ_type in layman_util.get_publication_types().values()
        }
    return _URL_NAME_TO_PUBLICATION_TYPE


def parse_request_path(request_path):
    workspace = None
    publication_type = None
    publication_type_url_prefix = None
    publication_name = None
    m = get_multipublication_path_pattern().match(request_path)
    if not m:
        m = get_workspace_multipublication_path_pattern().match(request_path)
    if not m:
        m = get_singlepublication_path_pattern().match(request_path)
    if m:
        workspace = m.groupdict().get('workspace', None)
        publication_type_url_prefix = m.group('publication_type')
        publication_name = m.groupdict().get('publication_name', None)
    if publication_type_url_prefix:
        publication_type = get_url_name_to_publication_type()[publication_type_url_prefix]['type']
    if workspace in settings.RESERVED_WORKSPACE_NAMES:
        workspace = None
        publication_type = None
        publication_name = None
    return workspace, publication_type, publication_name


def setup_patch_access_rights(request_form, kwargs):
    for type in ['read', 'write']:
        if request_form.get('access_rights.' + type):
            kwargs['access_rights'] = kwargs.get('access_rights', dict())
            access_rights = list({x.strip() for x in request_form['access_rights.' + type].split(',')})
            kwargs['access_rights'][type] = access_rights


def setup_post_access_rights(request_form, kwargs, actor_name):
    kwargs['access_rights'] = dict()
    for type in ['read', 'write']:
        if not request_form.get('access_rights.' + type):
            if actor_name:
                access_rights = [actor_name]
            else:
                access_rights = [settings.RIGHTS_EVERYONE_ROLE]
        else:
            access_rights = list({x.strip() for x in request_form['access_rights.' + type].split(',')})
        kwargs['access_rights'][type] = access_rights


def get_publications(publication_type, user, request_args):
    known_order_by_values = [consts.ORDER_BY_TITLE, consts.ORDER_BY_FULL_TEXT, ]

    full_text_filter = None
    if consts.FILTER_FULL_TEXT in request_args:
        full_text_filter = prime_db_schema_util.to_tsquery_string(request_args.get(consts.FILTER_FULL_TEXT)) or None

    order_by_list = []
    order_by_value = request_args.get(consts.ORDER_BY_PARAM)
    if order_by_value:
        if order_by_value not in known_order_by_values:
            raise LaymanError(2, {'parameter': consts.ORDER_BY_PARAM, 'supported_values': known_order_by_values})

        if order_by_value == consts.ORDER_BY_FULL_TEXT and not full_text_filter:
            raise LaymanError(48, f'Value "{consts.ORDER_BY_FULL_TEXT}" of parameter "{consts.ORDER_BY_PARAM}" can be '
                                  f'used only if "{consts.FILTER_FULL_TEXT}" parameter is set.')

        order_by_list.append(order_by_value)

    ordering_full_text = None
    if not order_by_list:
        if full_text_filter:
            ordering_full_text = full_text_filter
            order_by_list = [consts.ORDER_BY_FULL_TEXT]

    publication_infos_whole = layman_util.get_publication_infos(publ_type=publication_type,
                                                                context={'actor_name': user,
                                                                         'access_type': 'read'
                                                                         },
                                                                full_text_filter=full_text_filter,
                                                                order_by_list=order_by_list,
                                                                ordering_full_text=ordering_full_text,
                                                                )

    infos = [
        {
            'name': name,
            'workspace': workspace,
            'title': info.get("title"),
            'url': layman_util.get_workspace_publication_url(publication_type, workspace, name),
            'uuid': info["uuid"],
            'access_rights': info['access_rights'],
        }
        for (workspace, _, name), info in publication_infos_whole.items()
    ]
    return jsonify(infos), 200
