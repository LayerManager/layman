import pytest
from tests import Publication4Test
from tests.dynamic_data.base_test import RestMethod, WithChunksDomain, CompressDomain, Parametrization
from .util import format_exception


@pytest.mark.parametrize('exception_info, publication, parametrization, exp_result', [
    pytest.param(
        {'data': {'path': '{path_prefix}file.shp'}},
        Publication4Test('some_workspace', 'layer', 'some_name'),
        Parametrization([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.TRUE]),
        {'data': {'path': 'temporary_zip_file.zip/file.shp'}},
        id='path_prefix;chunks=FALSE,compress=TRUE'),
    pytest.param(
        {'data': {'path': '{path_prefix}file.shp'}},
        Publication4Test('some_workspace', 'layer', 'some_name', uuid='d2816b8f-4be9-46c0-a5c4-8c305abdd4e2'),
        Parametrization([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.TRUE]),
        {'data': {'path': 'd2816b8f-4be9-46c0-a5c4-8c305abdd4e2.zip/file.shp'}},
        id='path_prefix;chunks=TRUE,compress=TRUE'),
    pytest.param(
        {'data': {'path': '{path_prefix}file.shp'}},
        Publication4Test('some_workspace', 'layer', 'some_name'),
        Parametrization([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.FALSE]),
        {'data': {'path': 'file.shp'}},
        id='path_prefix;chunks=TRUE,compress=FALSE'),
    pytest.param(
        {'data': {'path': '{path_prefix}file.shp'}},
        Publication4Test('some_workspace', 'layer', 'some_name'),
        Parametrization([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        {'data': {'path': 'file.shp'}},
        id='path_prefix;chunks=FALSE,compress=FALSE'),
])
def test_format_exception(exception_info: dict, publication, parametrization: Parametrization, exp_result):
    format_exception(exception_info, publication, parametrization)
    assert exception_info == exp_result
