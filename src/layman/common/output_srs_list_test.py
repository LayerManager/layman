import pytest

from layman import settings, app
from layman.layer.qgis import util as qgis_util, wms as qgis_wms
from test_tools import process, process_client, geoserver_client
from test_tools.mock.layman_classes import LayerMock


LAYERS_TO_DELETE_AFTER_TEST = []


OUTPUT_SRS_LIST = [4326, 3857, 32633, 32634, 3059, 5514, 3034, 3035, ]
assert all(isinstance(epsg_code, int) for epsg_code in OUTPUT_SRS_LIST)


def test_default_srs_list():
    assert set(settings.LAYMAN_OUTPUT_SRS_LIST) == {'EPSG:3857', 'EPSG:4326', 'EPSG:5514', 'EPSG:32633', 'EPSG:32634', 'EPSG:3034',
                                                    'EPSG:3035', 'EPSG:3059', }


@pytest.fixture(scope="module")
def delete_layer_after_test():
    def register_layer_to_delete(workspace, layername):
        LAYERS_TO_DELETE_AFTER_TEST.append((workspace, layername))
    yield register_layer_to_delete
    for workspace, layername in LAYERS_TO_DELETE_AFTER_TEST:
        process_client.delete_workspace_layer(workspace, layername)


@pytest.fixture(scope="module")
def ensure_layer(delete_layer_after_test):
    def ensure_layer_internal(workspace, layername, file_paths=None, style_file=None):
        if (workspace, layername) not in LAYERS_TO_DELETE_AFTER_TEST:
            response = process_client.publish_workspace_layer(workspace, layername, file_paths=file_paths, style_file=style_file)
            delete_layer_after_test(workspace, layername)
        else:
            response = process_client.patch_workspace_layer(workspace, layername, file_paths=file_paths, style_file=style_file)
        return response
    yield ensure_layer_internal


@pytest.mark.timeout(40)
def test_custom_srs_list(ensure_layer):
    workspace = 'test_custom_srs_list_workspace'
    name_sld1 = 'test_custom_srs_list_sld_layer1'
    name_sld2 = 'test_custom_srs_list_sld_layer2'
    name_qgis1 = 'test_custom_srs_list_qgis_layer1'
    name_qgis2 = 'test_custom_srs_list_qgis_layer2'
    source_style_file_path = 'sample/style/small_layer.qml'
    output_crs_list = {f'EPSG:{srid}' for srid in OUTPUT_SRS_LIST}
    assert settings.LAYMAN_OUTPUT_SRS_LIST != output_crs_list

    process.ensure_layman_function(process.LAYMAN_DEFAULT_SETTINGS)
    uuid_sld1 = ensure_layer(workspace, name_sld1)['uuid']
    uuid_qgis1 = ensure_layer(workspace, name_qgis1, style_file=source_style_file_path)['uuid']

    sld1_layer = LayerMock(uuid=uuid_sld1, layer_tuple=(workspace, name_sld1))
    qgis1_layer = LayerMock(uuid=uuid_qgis1, layer_tuple=(workspace, name_qgis1))

    wfs_name_sld1 = sld1_layer.gs_names.wfs
    wfs_name_qgis1 = qgis1_layer.gs_names.wfs

    with app.app_context():
        init_output_epsg_codes_set = {crs.replace(':', '::') for crs in settings.LAYMAN_OUTPUT_SRS_LIST}
        assert_gs_wms_output_srs_list(wfs_name_sld1.workspace, wfs_name_sld1.name, settings.LAYMAN_OUTPUT_SRS_LIST)
        assert_wfs_output_srs_list(wfs_name_sld1.workspace, wfs_name_sld1.name, init_output_epsg_codes_set)
        assert not qgis_wms.get_layer_info(workspace, name_sld1)

        assert_gs_wms_output_srs_list(wfs_name_qgis1.workspace, wfs_name_qgis1.name, settings.LAYMAN_OUTPUT_SRS_LIST)
        assert_wfs_output_srs_list(wfs_name_qgis1.workspace, wfs_name_qgis1.name, init_output_epsg_codes_set)
        assert_qgis_output_srs_list(uuid_qgis1, settings.LAYMAN_OUTPUT_SRS_LIST)
        assert_qgis_wms_output_srs_list(qgis1_layer.qgis_names.name, uuid_qgis1, settings.LAYMAN_OUTPUT_SRS_LIST)

    process.ensure_layman_function({
        'LAYMAN_OUTPUT_SRS_LIST': ','.join([str(code) for code in OUTPUT_SRS_LIST])
    })
    uuid_sld2 = ensure_layer(workspace, name_sld2)['uuid']
    sld2_layer = LayerMock(uuid=uuid_sld2, layer_tuple=(workspace, name_sld2))
    uuid_qgis2 = ensure_layer(workspace, name_qgis2, style_file=source_style_file_path)['uuid']
    qgis2_layer = LayerMock(uuid=uuid_qgis2, layer_tuple=(workspace, name_qgis2))

    output_epsg_codes_set = {crs.replace(':', '::') for crs in output_crs_list}
    with app.app_context():
        for sld_layer in [sld1_layer, sld2_layer, ]:
            wfs_name_sld = sld_layer.gs_names.wfs
            assert_gs_wms_output_srs_list(wfs_name_sld.workspace, wfs_name_sld.name, output_crs_list)
            assert_wfs_output_srs_list(wfs_name_sld.workspace, wfs_name_sld.name, output_epsg_codes_set)
            assert not qgis_wms.get_layer_info(workspace, sld_layer.name)
        for qgis2_layer in [qgis1_layer, qgis2_layer, ]:
            wfs_name_qgis = qgis2_layer.gs_names.wfs
            assert_gs_wms_output_srs_list(wfs_name_qgis.workspace, wfs_name_qgis.name, output_crs_list)
            assert_wfs_output_srs_list(wfs_name_qgis.workspace, wfs_name_qgis.name, output_epsg_codes_set)
            assert_qgis_output_srs_list(uuid_qgis1, output_crs_list)
            assert_qgis_wms_output_srs_list(qgis1_layer.qgis_names.name, uuid_qgis1, output_crs_list)


def assert_gs_wms_output_srs_list(workspace, layername, expected_output_crs_list):
    wms = geoserver_client.get_wms_capabilities(workspace)
    assert layername in wms.contents
    wms_layer = wms.contents[layername]
    for expected_output_crs in expected_output_crs_list:
        assert expected_output_crs in wms_layer.crsOptions


def assert_qgis_wms_output_srs_list(qgis_layername, publ_uuid, expected_output_srs_list):
    wms = qgis_wms.get_wms_capabilities(publ_uuid)
    assert qgis_layername in wms.contents
    wms_layer = wms.contents[qgis_layername]
    for expected_output_srs in expected_output_srs_list:
        assert expected_output_srs in wms_layer.crsOptions


def assert_wfs_output_srs_list(workspace, layername, expected_output_epsg_codes):
    wfs = geoserver_client.get_wfs_capabilities(workspace)
    full_layername = f"{workspace}:{layername}"
    assert full_layername in wfs.contents
    wfs_layer = wfs.contents[full_layername]
    crs_names = [str(crs) for crs in wfs_layer.crsOptions]
    for expected_output_srs in expected_output_epsg_codes:
        assert f"urn:ogc:def:crs:{expected_output_srs}" in crs_names


def assert_qgis_output_srs_list(publ_uuid, expected_srs_list):
    with app.app_context():
        assert qgis_util.get_layer_wms_crs_list_values(publ_uuid) == set(expected_srs_list)
