from collections import namedtuple

REQUEST_METHOD_DELETE = 'delete'
REQUEST_METHOD_GET = 'get'
REQUEST_METHOD_PATCH = 'patch'
REQUEST_METHOD_POST = 'post'
REQUEST_METHOD_PUT = 'put'

PUBLICATION_LOCK_POST = REQUEST_METHOD_POST
PUBLICATION_LOCK_PATCH = REQUEST_METHOD_PATCH
PUBLICATION_LOCK_DELETE = REQUEST_METHOD_DELETE
PUBLICATION_LOCK_FEATURE_CHANGE = 'feature_change'

InternalSourceTypeDef = namedtuple('InternalSourceTypeDef', ['info_items',
                                                             ])


def empty_method(*_args, **_kwargs):
    pass


def empty_method_returns_none(*_args, **_kwargs):
    return None


def empty_method_returns_dict(*_args, **_kwargs):
    return {}


def empty_method_returns_true(*_args, **_kwargs):
    return True
