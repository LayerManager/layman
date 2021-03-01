import re

from layman import settings
from .util import PUBLICATION_NAME_ONLY_PATTERN
from layman.util import USERNAME_ONLY_PATTERN, get_publication_types


def _get_multi_publication_path_pattern():
    workspace_pattern = r"(?P<workspace>" + USERNAME_ONLY_PATTERN + r")"
    publ_type_names = [publ_type['rest_path_name'] for publ_type in get_publication_types().values()]
    publ_type_pattern = r"(?P<publication_type>" + "|".join(publ_type_names) + r")"
    return f"^/rest/({settings.REST_WORKSPACES_PREFIX}/)?" + workspace_pattern + "/" + publ_type_pattern


_MULTI_PUBLICATION_PATH_PATTERN = None
_SINGLE_PUBLICATION_PATH_PATTERN = None
_URL_NAME_TO_PUBLICATION_TYPE = None


def get_multipublication_path_pattern():
    global _MULTI_PUBLICATION_PATH_PATTERN
    if _MULTI_PUBLICATION_PATH_PATTERN is None:
        _MULTI_PUBLICATION_PATH_PATTERN = re.compile(_get_multi_publication_path_pattern() + r"/?$")
    return _MULTI_PUBLICATION_PATH_PATTERN


def get_singlepublication_path_pattern():
    global _SINGLE_PUBLICATION_PATH_PATTERN
    if _SINGLE_PUBLICATION_PATH_PATTERN is None:
        _SINGLE_PUBLICATION_PATH_PATTERN = re.compile(
            _get_multi_publication_path_pattern()
            + r"/(?P<publication_name>" + PUBLICATION_NAME_ONLY_PATTERN + r")(?:/.*)?$"
        )
    return _SINGLE_PUBLICATION_PATH_PATTERN


def get_url_name_to_publication_type():
    global _URL_NAME_TO_PUBLICATION_TYPE
    if _URL_NAME_TO_PUBLICATION_TYPE is None:
        _URL_NAME_TO_PUBLICATION_TYPE = {
            publ_type['rest_path_name']: publ_type
            for publ_type in get_publication_types().values()
        }
    return _URL_NAME_TO_PUBLICATION_TYPE


def parse_request_path(request_path):
    workspace = None
    publication_type = None
    publication_type_url_prefix = None
    publication_name = None
    m = get_multipublication_path_pattern().match(request_path)
    if not m:
        m = get_singlepublication_path_pattern().match(request_path)
    if m:
        workspace = m.group('workspace')
        publication_type_url_prefix = m.group('publication_type')
        publication_name = m.groupdict().get('publication_name', None)
    if publication_type_url_prefix:
        publication_type = get_url_name_to_publication_type()[publication_type_url_prefix]['type']
    if workspace in settings.RESERVED_WORKSPACE_NAMES:
        workspace = None
        publication_type = None
        publication_name = None
    return (workspace, publication_type, publication_name)


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
