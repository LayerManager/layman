from flask import g, request

from layman import LaymanError


def authorize():
    if request.method not in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
        raise LaymanError(31, {'method': request.method})
    pass


