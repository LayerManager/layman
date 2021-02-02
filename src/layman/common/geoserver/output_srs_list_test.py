import pytest
from layman import settings
from test import process, process_client, geoserver_client


LAYERS_TO_DELETE_AFTER_TEST = []


OUTPUT_SRS_LIST = [4326, 3857, 32633, 32634, 3059, 5514]


def test_default_srs_list():
    assert settings.LAYMAN_OUTPUT_SRS_LIST == [4326, 3857, 5514]


@pytest.fixture(scope="module")
def delete_layer_after_test():
    def register_layer_to_delete(workspace, layername):
        LAYERS_TO_DELETE_AFTER_TEST.append((workspace, layername))
    yield register_layer_to_delete
    for workspace, layername in LAYERS_TO_DELETE_AFTER_TEST:
        process_client.delete_layer(workspace, layername)


@pytest.fixture(scope="module")
def ensure_layer(delete_layer_after_test):
    def ensure_layer_internal(workspace, layername, file_paths=None):
        if (workspace, layername) not in LAYERS_TO_DELETE_AFTER_TEST:
            process_client.publish_layer(workspace, layername, file_paths=file_paths)
            delete_layer_after_test(workspace, layername)
    yield ensure_layer_internal


def test_custom_srs_list(ensure_layer):
    workspace = 'test_custom_srs_list_workspace'
    layername1 = 'test_custom_srs_list_layer1'
    layername2 = 'test_custom_srs_list_layer2'
    assert settings.LAYMAN_OUTPUT_SRS_LIST != OUTPUT_SRS_LIST

    process.ensure_layman_function(process.LAYMAN_DEFAULT_SETTINGS)
    ensure_layer(workspace, layername1)
    assert_wms_output_srs_list(workspace, layername1, settings.LAYMAN_OUTPUT_SRS_LIST)
    assert_wfs_output_srs_list(workspace, layername1, settings.LAYMAN_OUTPUT_SRS_LIST)

    process.ensure_layman_function({
        'LAYMAN_OUTPUT_SRS_LIST': ','.join([str(code) for code in OUTPUT_SRS_LIST])
    })
    ensure_layer(workspace, layername2)
    for layername in [layername1, layername2]:
        assert_wms_output_srs_list(workspace, layername, OUTPUT_SRS_LIST)
        assert_wfs_output_srs_list(workspace, layername, OUTPUT_SRS_LIST)


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


# expected coordinates manually copied from QGIS 3.16.2 in given EPSG
# point_id 1: northernmost vertex of fountain at Moravske namesti, Brno
@pytest.mark.parametrize('point_id, epsg_code, exp_coordinates, precision', [
    (1, 3857, (1848649.486, 6308703.297), 0.2),
    # ~5 meters! By default, GeoServer limits WFS output to 4 decimal places, about 10 m accuracy
    (1, 4326, (16.60669976, 49.19904767), 0.00005),
    (1, 32633, (617046.8503, 5450825.7990), 0.1),
    (1, 32634, (179991.0748, 5458879.0878), 0.1),
    (1, 5514, (-598208.8093, -1160307.4484), 0.1),
])
def test_spatial_precision(ensure_layer, point_id, epsg_code, exp_coordinates, precision):
    process.ensure_layman_function({
        'LAYMAN_OUTPUT_SRS_LIST': ','.join([str(code) for code in OUTPUT_SRS_LIST])
    })
    workspace = 'test_coordinate_precision_workspace'
    layername = 'test_coordinate_precision_layer'

    ensure_layer(workspace, layername, file_paths=['sample/layman.layer/sample_point_cz.geojson'])

    feature_collection = geoserver_client.get_features(workspace, layername, epsg_code=epsg_code)
    feature = next(f for f in feature_collection['features'] if f['properties']['point_id'] == point_id)
    for idx, coordinate in enumerate(feature['geometry']['coordinates']):
        assert abs(coordinate - exp_coordinates[idx]) <= precision, f"EPSG:{epsg_code}: expected coordinates={exp_coordinates}, found coordinates={feature['geometry']['coordinates']}"
