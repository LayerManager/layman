import re
from flask import jsonify, make_response

import crs as crs_def
from layman import settings, util as layman_util, LaymanError
from layman.authn import is_user_with_name
from layman.common import bbox as bbox_util
from .util import PUBLICATION_NAME_ONLY_PATTERN
from . import get_publications_consts as consts


def _get_pub_type_pattern():
    publ_type_names = [publ_type['rest_path_name'] for publ_type in layman_util.get_publication_types().values()]
    publ_type_pattern = r"(?P<publication_type>" + "|".join(publ_type_names) + r")"
    return publ_type_pattern


def _get_workspace_multi_publication_path_pattern():
    workspace_pattern = r"(?P<workspace>" + layman_util.WORKSPACE_NAME_ONLY_PATTERN + r")"
    return f"^/rest/({settings.REST_WORKSPACES_PREFIX}/)?" + workspace_pattern + "/" + _get_pub_type_pattern()


_MULTI_PUBLICATION_PATH_PATTERN = layman_util.SimpleStorage()
_WORKSPACE_MULTI_PUBLICATION_PATH_PATTERN = layman_util.SimpleStorage()
_WORKSPACE_SINGLE_PUBLICATION_PATH_PATTERN = layman_util.SimpleStorage()
_URL_NAME_TO_PUBLICATION_TYPE = layman_util.SimpleStorage()


def get_multipublication_path_pattern():
    if _MULTI_PUBLICATION_PATH_PATTERN.get() is None:
        _MULTI_PUBLICATION_PATH_PATTERN.set(re.compile(f"^/rest/" + _get_pub_type_pattern() + r"/?$"))
    return _MULTI_PUBLICATION_PATH_PATTERN.get()


def get_workspace_multipublication_path_pattern():
    if _WORKSPACE_MULTI_PUBLICATION_PATH_PATTERN.get() is None:
        _WORKSPACE_MULTI_PUBLICATION_PATH_PATTERN.set(re.compile(_get_workspace_multi_publication_path_pattern() + r"/?$"))
    return _WORKSPACE_MULTI_PUBLICATION_PATH_PATTERN.get()


def get_singlepublication_path_pattern():
    if _WORKSPACE_SINGLE_PUBLICATION_PATH_PATTERN.get() is None:
        _WORKSPACE_SINGLE_PUBLICATION_PATH_PATTERN.set(re.compile(
            _get_workspace_multi_publication_path_pattern()
            + r"/(?P<publication_name>" + PUBLICATION_NAME_ONLY_PATTERN + r")(?:/.*)?$"
        ))
    return _WORKSPACE_SINGLE_PUBLICATION_PATH_PATTERN.get()


def get_url_name_to_publication_type():
    if _URL_NAME_TO_PUBLICATION_TYPE.get() is None:
        _URL_NAME_TO_PUBLICATION_TYPE.set({
            publ_type['rest_path_name']: publ_type
            for publ_type in layman_util.get_publication_types().values()
        })
    return _URL_NAME_TO_PUBLICATION_TYPE.get()


def parse_request_path(request_path):
    workspace = None
    publication_type = None
    publication_type_url_prefix = None
    publication_name = None
    match = get_multipublication_path_pattern().match(request_path)
    if not match:
        match = get_workspace_multipublication_path_pattern().match(request_path)
    if not match:
        match = get_singlepublication_path_pattern().match(request_path)
    if match:
        workspace = match.groupdict().get('workspace', None)
        publication_type_url_prefix = match.group('publication_type')
        publication_name = match.groupdict().get('publication_name', None)
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
            if is_user_with_name(actor_name):
                access_rights = [actor_name]
            else:
                access_rights = [settings.RIGHTS_EVERYONE_ROLE]
        else:
            access_rights = list({x.strip() for x in request_form['access_rights.' + type].split(',')})
        kwargs['access_rights'][type] = access_rights


def get_bbox_from_param(request_args, param_name):
    bbox = None
    if request_args.get(param_name):
        match = re.match(consts.BBOX_PATTERN, request_args[param_name])
        if not match:
            raise LaymanError(2, {'parameter': param_name, 'expected': {
                'text': 'Four comma-separated coordinates: minx,miny,maxx,maxy',
                'regular_expression': consts.BBOX_PATTERN,
            }})
        coords = tuple(float(c) for c in match.groups())
        if not bbox_util.is_valid(coords):
            raise LaymanError(2, {'parameter': param_name, 'expected': 'minx <= maxx and miny <= maxy'})
        bbox = coords
    return bbox


def get_crs_from_param(request_args, param_name):
    crs = None
    if request_args.get(param_name):
        match = re.match(consts.CRS_PATTERN, request_args[param_name])
        if not match:
            raise LaymanError(2, {'parameter': param_name, 'expected': {
                'text': 'One CRS name: AUTHORITY:CODE',
                'regular_expression': consts.CRS_PATTERN,
            }})
        crs = match.groups()[0]
        if crs not in settings.LAYMAN_OUTPUT_SRS_LIST:
            raise LaymanError(2, {'parameter': param_name, 'expected': settings.LAYMAN_OUTPUT_SRS_LIST, 'value': crs})
    return crs


def get_integer_from_param(request_args, param_name, negative=True, zero=True, positive=True):
    result = None
    assert negative or zero or positive
    if request_args.get(param_name):
        match = re.match(consts.INTEGER_PATTERN, request_args[param_name])
        if not match:
            raise LaymanError(2, {'parameter': param_name, 'expected': {
                'text': 'Integer with optional sign',
                'regular_expression': consts.INTEGER_PATTERN,
            }})
        integer = int(match.groups()[0])

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


def get_publications(publication_type, actor, request_args=None, workspace=None):
    request_args = request_args or {}
    known_order_by_values = [consts.ORDER_BY_TITLE, consts.ORDER_BY_FULL_TEXT, consts.ORDER_BY_LAST_CHANGE,
                             consts.ORDER_BY_BBOX, ]

    #########################################################
    # Filters
    full_text_filter = None
    if consts.FILTER_FULL_TEXT in request_args:
        full_text_filter = request_args[consts.FILTER_FULL_TEXT].strip() or None

    bbox_filter = get_bbox_from_param(request_args, consts.FILTER_BBOX)
    bbox_filter_crs = get_crs_from_param(request_args, consts.FILTER_BBOX_CRS)

    bbox_filter_crs = bbox_filter_crs or (crs_def.EPSG_3857 if bbox_filter else None)

    #########################################################
    # Ordering
    ordering_bbox = get_bbox_from_param(request_args, consts.ORDERING_BBOX)
    ordering_bbox_crs = get_crs_from_param(request_args, consts.ORDERING_BBOX_CRS)

    ordering_bbox_crs = ordering_bbox_crs or ((bbox_filter_crs or crs_def.EPSG_3857) if ordering_bbox else None)

    explicit_order_by_value = request_args.get(consts.ORDER_BY_PARAM)
    if explicit_order_by_value:
        if explicit_order_by_value not in known_order_by_values:
            raise LaymanError(2, {'parameter': consts.ORDER_BY_PARAM, 'supported_values': known_order_by_values})
        order_by_value = explicit_order_by_value
    # Set ordering by other parameters if not specified by request
    elif full_text_filter:
        order_by_value = consts.ORDER_BY_FULL_TEXT
    elif bbox_filter or ordering_bbox:
        order_by_value = consts.ORDER_BY_BBOX
    else:
        order_by_value = None

    if order_by_value == consts.ORDER_BY_BBOX and not ordering_bbox:
        ordering_bbox = bbox_filter
        ordering_bbox_crs = bbox_filter_crs

    ordering_full_text = full_text_filter if order_by_value == consts.ORDER_BY_FULL_TEXT else None

    order_by_list = [order_by_value] if order_by_value else []

    #########################################################
    # Checking parameters combination
    if explicit_order_by_value == consts.ORDER_BY_FULL_TEXT and not full_text_filter:
        raise LaymanError(48, f'Value "{consts.ORDER_BY_FULL_TEXT}" of parameter "{consts.ORDER_BY_PARAM}" can be '
                              f'used only if "{consts.FILTER_FULL_TEXT}" parameter is set.')

    if explicit_order_by_value == consts.ORDER_BY_BBOX and not bbox_filter and not ordering_bbox:
        raise LaymanError(48, f'Value "{consts.ORDER_BY_BBOX}" of parameter "{consts.ORDER_BY_PARAM}" can be '
                              f'used only if "{consts.FILTER_BBOX}" or "{consts.ORDER_BY_BBOX}" parameter is set.')

    if ordering_bbox and order_by_value != consts.ORDER_BY_BBOX:
        raise LaymanError(48, f'Parameter "{consts.ORDERING_BBOX}" can be set only if '
                              f'parameter "{consts.ORDER_BY_PARAM}" is set to {consts.ORDER_BY_BBOX}.')

    if bbox_filter_crs and not bbox_filter:
        raise LaymanError(48, f'Parameter "{consts.FILTER_BBOX_CRS}" can be set only if '
                              f'parameter "{consts.FILTER_BBOX}" is set.')

    if ordering_bbox_crs and not ordering_bbox:
        raise LaymanError(48, f'Parameter "{consts.ORDERING_BBOX_CRS}" can be set only if '
                              f'parameter "{consts.ORDERING_BBOX}" is set.')

    #########################################################
    # Pagination
    limit = get_integer_from_param(request_args, consts.LIMIT, negative=False)
    offset = get_integer_from_param(request_args, consts.OFFSET, negative=False)

    #########################################################
    publication_infos_whole = layman_util.get_publication_infos_with_metainfo(publ_type=publication_type,
                                                                              workspace=workspace,
                                                                              context={'actor_name': actor,
                                                                                       'access_type': 'read'
                                                                                       },
                                                                              limit=limit, offset=offset,
                                                                              full_text_filter=full_text_filter,
                                                                              bbox_filter=bbox_filter,
                                                                              bbox_filter_crs=bbox_filter_crs,
                                                                              order_by_list=order_by_list,
                                                                              ordering_full_text=ordering_full_text,
                                                                              ordering_bbox=ordering_bbox,
                                                                              ordering_bbox_crs=ordering_bbox_crs
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
            'native_crs': info['native_crs'],
            'native_bounding_box': info['native_bounding_box'],
            'geodata_type': info['geodata_type'],
            'file': {
                'file_type': info['geodata_type'],
            },
        }
        for (workspace, _, name), info in publication_infos_whole['items'].items()
    ]

    multi_info_keys_to_remove = layman_util.get_multi_info_keys_to_remove(publication_type)
    for info in infos:
        for info_key_to_remove in multi_info_keys_to_remove:
            info.pop(info_key_to_remove, None)

    response = make_response(jsonify(infos), 200)
    response.headers['X-Total-Count'] = publication_infos_whole['total_count']
    response.headers['Content-Range'] = f'items {publication_infos_whole["content_range"][0]}-' \
                                        f'{publication_infos_whole["content_range"][1]}/{publication_infos_whole["total_count"]}'
    return response
