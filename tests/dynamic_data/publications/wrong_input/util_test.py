import pytest
from tests import Publication
from tests.dynamic_data.base_test import RestMethod, WithChunksDomain, CompressDomain, Parametrization
from .util import case_to_simple_parametrizations, format_exception


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


@pytest.mark.parametrize('exception_info, publication, parametrization, exp_result', [
    pytest.param(
        {'data': {'path': '{path_prefix}file.shp'}},
        Publication('some_workspace', 'layer', 'some_name'),
        Parametrization([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.TRUE]),
        {'data': {'path': 'temporary_zip_file.zip/file.shp'}},
        id='path_prefix;chunks=FALSE,compress=TRUE'),
    pytest.param(
        {'data': {'path': '{path_prefix}file.shp'}},
        Publication('some_workspace', 'layer', 'some_name'),
        Parametrization([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.TRUE]),
        {'data': {'path': 'some_name.zip/file.shp'}},
        id='path_prefix;chunks=TRUE,compress=TRUE'),
    pytest.param(
        {'data': {'path': '{path_prefix}file.shp'}},
        Publication('some_workspace', 'layer', 'some_name'),
        Parametrization([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.FALSE]),
        {'data': {'path': 'file.shp'}},
        id='path_prefix;chunks=TRUE,compress=FALSE'),
    pytest.param(
        {'data': {'path': '{path_prefix}file.shp'}},
        Publication('some_workspace', 'layer', 'some_name'),
        Parametrization([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        {'data': {'path': 'file.shp'}},
        id='path_prefix;chunks=FALSE,compress=FALSE'),
])
def test_format_exception(exception_info: dict, publication, parametrization: Parametrization, exp_result):
    format_exception(exception_info, publication, parametrization)
    assert exception_info == exp_result
