import types
import logging
import traceback
from functools import partial
from requests.exceptions import HTTPError, ConnectionError
from .http import LaymanError

logger = logging.getLogger(__name__)


def decorate_all_in_module(module, decorator):
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, types.FunctionType):
            setattr(module, name, decorator(obj))


def error_handling_decorator(raise_as, func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as exc:
            logger.warning(f'traceback={traceback.format_exc()},\n'
                           f'response={exc.response.text},\n'
                           f'http_code={exc.response.status_code}')
            raise LaymanError(raise_as,
                              data={'caused_by': exc.__class__.__name__, 'http_code': exc.response.status_code},
                              private_data={'response_text': exc.response.text}) from exc
        except ConnectionError as exc:
            logger.warning(traceback.format_exc())
            raise LaymanError(raise_as) from exc

    return inner


def get_handler_for_error(raise_as):
    return partial(error_handling_decorator, raise_as)
