import pytest
from tests.dynamic_data import base_test
from .util import case_to_simple_parametrizations


@pytest.mark.parametrize('input, exp_result', [
    pytest.param(None, set(), id='None'),
    pytest.param(
        frozenset([base_test.RestMethod, base_test.WithChunksDomain, base_test.CompressDomain]),
        {
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
            frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.FALSE]),
            frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
            frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.FALSE, base_test.CompressDomain.TRUE]),
            frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.TRUE]),
        },
        id='three_domains'),
    pytest.param(
        frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        {frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE])},
        id='three_values'),
    pytest.param(
        frozenset([base_test.RestMethod, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        {
            frozenset([base_test.RestMethod.POST, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
            frozenset([base_test.RestMethod.PATCH, base_test.WithChunksDomain.TRUE, base_test.CompressDomain.FALSE]),
        },
        id='two_values_one_domain'),
])
def test_case_to_simple_parametrizations(input, exp_result):
    result = case_to_simple_parametrizations(input)
    assert result == exp_result
