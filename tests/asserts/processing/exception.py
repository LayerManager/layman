from test_tools import util as test_util


def response_exception(expected, thrown):
    test_util.assert_error(expected, thrown)
