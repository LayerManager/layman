import re

from layman import settings
from .util import PUBLICATION_NAME_ONLY_PATTERN
from layman.util import USERNAME_ONLY_PATTERN


def _get_multi_publication_path_pattern():
    workspace_pattern = r"(?P<workspace>" + USERNAME_ONLY_PATTERN + r")"
    # TODO generate layers|maps automatically from blueprints using settings.PUBLICATION_MODULES
    publ_type_pattern = r"(?P<publication_type>layers|maps)"
    return "^/rest/" + workspace_pattern + "/" + publ_type_pattern


MULTI_PUBLICATION_PATH_PATTERN = re.compile(_get_multi_publication_path_pattern() + r"/?$")
SINGLE_PUBLICATION_PATH_PATTERN = re.compile(
    _get_multi_publication_path_pattern() + r"/(?P<publication_name>" + PUBLICATION_NAME_ONLY_PATTERN + r")(?:/.*)?$"
)


def parse_request_path(request_path):
    workspace = None
    publication_type = None
    publication_type_url_prefix = None
    publication_name = None
    m = MULTI_PUBLICATION_PATH_PATTERN.match(request_path)
    if not m:
        m = SINGLE_PUBLICATION_PATH_PATTERN.match(request_path)
    if m:
        workspace = m.group('workspace')
        publication_type_url_prefix = m.group('publication_type')
        publication_name = m.groupdict().get('publication_name', None)
    if publication_type_url_prefix:
        # TODO get it using settings.PUBLICATION_MODULES
        publication_type = {
            'layers': 'layman.layer',
            'maps': 'layman.map',
        }[publication_type_url_prefix]
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
