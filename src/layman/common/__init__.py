from collections import namedtuple

InternalSourceTypeDef = namedtuple('InternalSourceTypeDef', ['info_items',
                                                             ])


def empty_method(*_args, **_kwargs):
    pass


def empty_method_returns_none(*_args, **_kwargs):
    return None


def empty_method_returns_dict(*_args, **_kwargs):
    return dict()


def empty_method_returns_true(*_args, **_kwargs):
    return True
