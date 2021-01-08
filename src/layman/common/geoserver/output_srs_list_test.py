import pytest
from layman import settings, app
from layman.util import url_for
from test import process, process_client
from layman.layer.geoserver.util import wms_direct, wfs_direct


LAYERS_TO_DELETE_AFTER_TEST = []


def test_default_srs_list():
    assert settings.LAYMAN_OUTPUT_SRS_LIST == [4326, 3857]


@pytest.fixture(scope="module")
def delete_layer_after_test():
    def register_layer_to_delete(workspace, layername):
        LAYERS_TO_DELETE_AFTER_TEST.append((workspace, layername))
    yield register_layer_to_delete
    for workspace, layername in LAYERS_TO_DELETE_AFTER_TEST:
        process_client.delete_layer(workspace, layername)


def test_custom_srs_list(delete_layer_after_test):
    workspace = 'test_custom_srs_list_workspace'
    layername = 'test_custom_srs_list_layer'
    output_srs_list = [4326, 3857, 32633, 32634, 3059]
    process.ensure_layman_function({
        'LAYMAN_OUTPUT_SRS_LIST': ','.join([str(code) for code in output_srs_list])
    })
    process_client.publish_layer(workspace, layername)
    delete_layer_after_test(workspace, layername)
    assert_wms_output_srs_list(workspace, layername, output_srs_list)
    assert_wfs_output_srs_list(workspace, layername, output_srs_list)


def assert_wms_output_srs_list(workspace, layername, expected_output_srs_list):
    with app.app_context():
        wms_url = url_for('gs_wfs_proxy_bp.proxy', subpath=workspace + '/' + 'ows')
    wms = wms_direct(wms_url)
    assert layername in wms.contents
    wms_layer = wms.contents[layername]
    for expected_output_srs in expected_output_srs_list:
        assert f"EPSG:{expected_output_srs}" in wms_layer.crsOptions


def assert_wfs_output_srs_list(workspace, layername, expected_output_srs_list):
    with app.app_context():
        wfs_url = url_for('gs_wfs_proxy_bp.proxy', subpath=workspace + '/' + 'wfs')
    wfs = wfs_direct(wfs_url)
    full_layername = f"{workspace}:{layername}"
    assert full_layername in wfs.contents
    wfs_layer = wfs.contents[full_layername]
    crs_names = [str(crs) for crs in wfs_layer.crsOptions]
    for expected_output_srs in expected_output_srs_list:
        assert f"urn:ogc:def:crs:EPSG::{expected_output_srs}" in crs_names
