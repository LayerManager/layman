import pytest

from layman import LaymanError
from test_tools import process_client


@pytest.mark.parametrize('query_params, error_code, error_specification,', [
    ({'order_by': 'gdasfda'}, (2, 400), {'parameter': 'order_by'}),
    ({'order_by': 'full_text'}, (48, 400), {}),
    ({'order_by': 'bbox'}, (48, 400), {}),
    ({'order_by': 'title', 'ordering_bbox': '1,2,3,4'}, (48, 400), {}),
    ({'bbox_filter': '1,2,3,4,5'}, (2, 400), {'parameter': 'bbox_filter'}),
    ({'bbox_filter': '1,2,c,4'}, (2, 400), {'parameter': 'bbox_filter'}),
    ({'bbox_filter': '1,4,2,3'}, (2, 400), {'parameter': 'bbox_filter'}),
    ({'bbox_filter_crs': '3'}, (2, 400), {'parameter': 'bbox_filter_crs'}),
    ({'bbox_filter_crs': 'EPSG:3030'}, (2, 400), {'parameter': 'bbox_filter_crs'}),
    ({'bbox_filter_crs': 'CRS:84'}, (2, 400), {'parameter': 'bbox_filter_crs'}),
    ({'bbox_filter_crs': 'EPSG:3857'}, (48, 400), {}),
    ({'ordering_bbox': '1,2,3,4,5'}, (2, 400), {'parameter': 'ordering_bbox'}),
    ({'ordering_bbox': '1,2,c,4'}, (2, 400), {'parameter': 'ordering_bbox'}),
    ({'ordering_bbox': '1,4,2,3'}, (2, 400), {'parameter': 'ordering_bbox'}),
    ({'ordering_bbox_crs': 'EPSG:3857'}, (48, 400), {}),
    ({'limit': 'dasda'}, (2, 400), {'parameter': 'limit'}),
    ({'limit': '-7'}, (2, 400), {'parameter': 'limit'}),
    ({'offset': 'dasda'}, (2, 400), {'parameter': 'offset'}),
    ({'offset': '-7'}, (2, 400), {'parameter': 'offset'}),
])
@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('ensure_layman', )
def test_get_publications_errors(publication_type, query_params, error_code, error_specification):
    with pytest.raises(LaymanError) as exc_info:
        process_client.get_publications(publication_type, query_params=query_params)
    assert exc_info.value.code == error_code[0]
    assert exc_info.value.http_code == error_code[1]
    for key, value in error_specification.items():
        assert exc_info.value.data[key] == value, (exc_info, error_specification)
