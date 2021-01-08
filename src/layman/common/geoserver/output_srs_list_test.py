import pytest
from layman import settings
from test import process, process_client, geoserver_client


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


@pytest.mark.timeout(20)
def test_custom_srs_list(delete_layer_after_test):
    workspace = 'test_custom_srs_list_workspace'
    layername1 = 'test_custom_srs_list_layer1'
    layername2 = 'test_custom_srs_list_layer2'
    output_srs_list = [4326, 3857, 32633, 32634, 3059]
    assert settings.LAYMAN_OUTPUT_SRS_LIST != output_srs_list

    process.ensure_layman_function(process.LAYMAN_DEFAULT_SETTINGS)
    process_client.publish_layer(workspace, layername1)
    delete_layer_after_test(workspace, layername1)
    assert_wms_output_srs_list(workspace, layername1, settings.LAYMAN_OUTPUT_SRS_LIST)
    assert_wfs_output_srs_list(workspace, layername1, settings.LAYMAN_OUTPUT_SRS_LIST)

    process.ensure_layman_function({
        'LAYMAN_OUTPUT_SRS_LIST': ','.join([str(code) for code in output_srs_list])
    })
    process_client.publish_layer(workspace, layername2)
    delete_layer_after_test(workspace, layername2)
    for layername in [layername1, layername2]:
        assert_wms_output_srs_list(workspace, layername, output_srs_list)
        assert_wfs_output_srs_list(workspace, layername, output_srs_list)


def assert_wms_output_srs_list(workspace, layername, expected_output_srs_list):
    wms = geoserver_client.get_wms_capabilities(workspace)
    assert layername in wms.contents
    wms_layer = wms.contents[layername]
    for expected_output_srs in expected_output_srs_list:
        assert f"EPSG:{expected_output_srs}" in wms_layer.crsOptions


def assert_wfs_output_srs_list(workspace, layername, expected_output_srs_list):
    wfs = geoserver_client.get_wfs_capabilities(workspace)
    full_layername = f"{workspace}:{layername}"
    assert full_layername in wfs.contents
    wfs_layer = wfs.contents[full_layername]
    crs_names = [str(crs) for crs in wfs_layer.crsOptions]
    for expected_output_srs in expected_output_srs_list:
        assert f"urn:ogc:def:crs:EPSG::{expected_output_srs}" in crs_names
