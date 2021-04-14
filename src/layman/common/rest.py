import re
from flask import jsonify

from layman import settings, util as layman_util, LaymanError
from layman.common.prime_db_schema import util as prime_db_schema_util
from layman.common import bbox as bbox_util
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


def get_bbox_from_param(request_args, param_name):
    bbox = None
    if request_args.get(param_name):
        m = re.match(consts.BBOX_PATTERN, request_args[param_name])
        if not m:
            raise LaymanError(2, {'parameter': param_name, 'expected': {
                'text': 'Four comma-separated coordinates: minx,miny,maxx,maxy',
                'regular_expression': consts.BBOX_PATTERN,
            }})
        coords = tuple(float(c) for c in m.groups())
        if not bbox_util.is_valid(coords):
            raise LaymanError(2, {'parameter': param_name, 'expected': 'minx <= maxx and miny <= maxy'})
        bbox = coords
    return bbox


def get_integer_from_param(request_args, param_name, negative=True, zero=True, positive=True):
    result = None
    assert negative or zero or positive
    if request_args.get(param_name):
        m = re.match(consts.INTEGER_PATTERN, request_args[param_name])
        if not m:
            raise LaymanError(2, {'parameter': param_name, 'expected': {
                'text': 'Integer with optional sign',
                'regular_expression': consts.INTEGER_PATTERN,
            }})
        integer = int(m.groups()[0])

        if integer < 0 and not negative:
            expected_than = '>' + ('=' if zero else '')
            raise LaymanError(2, {'parameter': param_name, 'expected': f'value {expected_than} 0'})
        if integer == 0 and not zero:
            expected_than = ('<' if negative else '') + ('>' if positive else '')
            raise LaymanError(2, {'parameter': param_name, 'expected': f'value {expected_than} 0'})
        if integer > 0 and not positive:
            expected_than = '<' + ('=' if zero else '')
            raise LaymanError(2, {'parameter': param_name, 'expected': f'value {expected_than} 0'})
        result = integer

    return result


def get_publications(publication_type, user, request_args=None, workspace=None):
    request_args = request_args or {}
    known_order_by_values = [consts.ORDER_BY_TITLE, consts.ORDER_BY_FULL_TEXT, consts.ORDER_BY_LAST_CHANGE,
                             consts.ORDER_BY_BBOX, ]

    full_text_filter = None
    if consts.FILTER_FULL_TEXT in request_args:
        full_text_filter = prime_db_schema_util.to_tsquery_string(request_args[consts.FILTER_FULL_TEXT]) or None

    bbox_filter = get_bbox_from_param(request_args, consts.FILTER_BBOX)
    ordering_bbox = get_bbox_from_param(request_args, consts.ORDERING_BBOX)

    order_by_value = request_args.get(consts.ORDER_BY_PARAM)
    if order_by_value:
        if order_by_value not in known_order_by_values:
            raise LaymanError(2, {'parameter': consts.ORDER_BY_PARAM, 'supported_values': known_order_by_values})

        if order_by_value == consts.ORDER_BY_FULL_TEXT and not full_text_filter:
            raise LaymanError(48, f'Value "{consts.ORDER_BY_FULL_TEXT}" of parameter "{consts.ORDER_BY_PARAM}" can be '
                                  f'used only if "{consts.FILTER_FULL_TEXT}" parameter is set.')
        if order_by_value == consts.ORDER_BY_BBOX and not bbox_filter and not ordering_bbox:
            raise LaymanError(48, f'Value "{consts.ORDER_BY_BBOX}" of parameter "{consts.ORDER_BY_PARAM}" can be '
                                  f'used only if "{consts.FILTER_BBOX}" or "{consts.ORDER_BY_BBOX}" parameter is set.')
    elif full_text_filter:
        order_by_value = consts.ORDER_BY_FULL_TEXT
    elif bbox_filter or ordering_bbox:
        order_by_value = consts.ORDER_BY_BBOX

    if ordering_bbox and order_by_value != consts.ORDER_BY_BBOX:
        raise LaymanError(48, f'Parameter "{consts.ORDERING_BBOX}" can be set only if '
                              f'parameter "{consts.ORDER_BY_PARAM}" is set to {consts.ORDER_BY_BBOX}.')

    ordering_full_text = full_text_filter if order_by_value == consts.ORDER_BY_FULL_TEXT else None

    if order_by_value == consts.ORDER_BY_BBOX and not ordering_bbox:
        ordering_bbox = bbox_filter

    order_by_list = [order_by_value] if order_by_value else []

    limit = get_integer_from_param(request_args, consts.LIMIT, negative=False)
    offset = get_integer_from_param(request_args, consts.OFFSET, negative=False)

    publication_infos_whole = layman_util.get_publication_infos(publ_type=publication_type,
                                                                workspace=workspace,
                                                                context={'actor_name': user,
                                                                         'access_type': 'read'
                                                                         },
                                                                limit=limit, offset=offset,
                                                                full_text_filter=full_text_filter,
                                                                bbox_filter=bbox_filter,
                                                                order_by_list=order_by_list,
                                                                ordering_full_text=ordering_full_text,
                                                                ordering_bbox=ordering_bbox,
                                                                )

    infos = [
        {
            'name': name,
            'workspace': workspace,
            'title': info.get("title"),
            'url': layman_util.get_workspace_publication_url(publication_type, workspace, name),
            'uuid': info["uuid"],
            'access_rights': info['access_rights'],
            'updated_at': info['updated_at'].isoformat(),
            'bounding_box': info['bounding_box'],
        }
        for (workspace, _, name), info in publication_infos_whole.items()
    ]
    return jsonify(infos), 200
