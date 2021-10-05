from .. import util as assert_util


def same_infos(expected, response):
    assert assert_util.same_infos(expected, response), f'expected={expected}, response={response}'
