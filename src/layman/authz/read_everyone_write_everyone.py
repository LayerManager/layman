from flask import g, request

from layman import LaymanError
from layman.common import geoserver as gs


def authorize():
    if request.method not in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        raise LaymanError(31, {'method': request.method})
    pass


def get_publication_access_rights(publ_type, username, publication_name):
    return {
        'guest': 'w',
    }


def get_GS_roles(username, type):
    if type == 'r':
        roles = gs.get_roles_anyone(username)
    elif type == 'w':
        roles = gs.get_roles_anyone(username)
    return roles
