from flask import g, request

from layman import LaymanError


def authorize():
    if request.method not in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        raise LaymanError(31, {'method': request.method})
    pass


def get_publication_access_rights(publ_type, username, publication_name):
    return {
        'guest': 'w',
    }
