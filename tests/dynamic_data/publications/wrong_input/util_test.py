import pytest
from tests.dynamic_data.base_test import RestMethod, WithChunksDomain, CompressDomain
from .util import case_to_simple_parametrizations


@pytest.mark.parametrize('input, exp_result', [
    pytest.param(None, set(), id='None'),
    pytest.param(
        frozenset([RestMethod, WithChunksDomain, CompressDomain]),
        {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
            frozenset([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.FALSE]),
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.TRUE]),
            frozenset([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.TRUE]),
            frozenset([RestMethod.PATCH, WithChunksDomain.FALSE, CompressDomain.FALSE]),
            frozenset([RestMethod.PATCH, WithChunksDomain.TRUE, CompressDomain.FALSE]),
            frozenset([RestMethod.PATCH, WithChunksDomain.FALSE, CompressDomain.TRUE]),
            frozenset([RestMethod.PATCH, WithChunksDomain.TRUE, CompressDomain.TRUE]),
        },
        id='three_domains'),
    pytest.param(
        frozenset([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.FALSE]),
        {frozenset([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.FALSE])},
        id='three_values'),
    pytest.param(
        frozenset([RestMethod, WithChunksDomain.TRUE, CompressDomain.FALSE]),
        {
            frozenset([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.FALSE]),
            frozenset([RestMethod.PATCH, WithChunksDomain.TRUE, CompressDomain.FALSE]),
        },
        id='two_values_one_domain'),
])
def test_case_to_simple_parametrizations(input, exp_result):
    result = case_to_simple_parametrizations(input)
    assert result == exp_result
