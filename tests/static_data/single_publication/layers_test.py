import os
from urllib.parse import urljoin
import difflib
import requests
from lxml import etree as ET
from owslib.wms import WebMapService
import pytest

import crs as crs_def
from geoserver import GS_REST_WORKSPACES, GS_REST, GS_AUTH, util as gs_util
from layman import settings, app, util as layman_util, names
from layman.common import bbox as bbox_util
from layman.common.micka import util as micka_common_util
from layman.layer import util as layer_util, db as layer_db, get_layer_info_keys
from layman.layer.geoserver.wms import DEFAULT_WMS_QGIS_STORE_PREFIX, VERSION
from layman.layer.layer_class import Layer
from layman.layer.micka import csw
from layman.layer.qgis import util as qgis_util
from test_tools import process_client, assert_util, geoserver_client
from test_tools.util import url_for
from .. import util
from ... import static_data as data
from ...asserts.final import publication as publ_asserts
from ..data import ensure_publication

headers_sld = {
    'Accept': 'application/vnd.ogc.sld+xml',
    'Content-type': 'application/xml',
}


@pytest.mark.timeout(600)
@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_info(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    wms_url = f"http://localhost:8000/geoserver/{names.GEOSERVER_WMS_WORKSPACE}/ows"
    wfs_url = f"http://localhost:8000/geoserver/{names.GEOSERVER_WFS_WORKSPACE}/wfs"
    headers = data.HEADERS.get(data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])
    style = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['style_type']

    info = process_client.get_workspace_publication(publ_type, workspace, publication, headers=headers)
    with app.app_context():
        info_internal = layer_util.get_layer_info(workspace, publication)
        expected_style_url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=publication,
                                     internal=False)

    file_type = info_internal['_file']['file_type']
    original_data_source = info.get('original_data_source', settings.EnumOriginalDataSource.FILE.value)
    item_keys = get_layer_info_keys(geodata_type=file_type, original_data_source=original_data_source)
    info_keys = set(info.keys())

    assert info_keys == item_keys, f'info={info}'
    assert info['wms'].get('url') == wms_url, f'r_json={info}, wms_url={wms_url}'
    assert 'url' in info['wms'], f'info={info}'
    if 'wfs' in info:
        assert info['wfs'].get('url') == wfs_url, f'r_json={info}, wfs_url={wfs_url}'

    assert info_internal['_style_type'] == style, f'info_internal={info_internal}'
    assert info['style']['type'] == style, info.get('style')
    external_style_url = info['style']['url']
    assert external_style_url == expected_style_url, (info, external_style_url)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_geoserver_workspace(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    headers = data.HEADERS.get(data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])

    publ_asserts.geoserver_proxy.is_complete_in_workspace_wms_1_3_0(workspace, publ_type, publication, headers)
    publ_asserts.geoserver_proxy.workspace_wfs_2_0_0_capabilities_available_if_vector(workspace, publ_type, publication, headers)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_get_layer_style(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    headers = data.HEADERS.get(data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])

    with app.app_context():
        rest_url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=publication)
    response = requests.get(rest_url, headers=headers, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert response.status_code == 200, response.text

    # lxml does not support importing from utf8 string
    xml_tree = ET.fromstring(bytes(response.text, encoding='utf8'))

    style_type = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['style_type']
    if style_type == 'sld':
        assert ET.QName(xml_tree) == "{http://www.opengis.net/sld}StyledLayerDescriptor", response.text
    elif style_type == 'qml':
        assert ET.QName(xml_tree), response.text
        assert ET.QName(xml_tree) == "qgis", response.text
        assert len(xml_tree.xpath('/qgis/renderer-v2')) == 1, response.text
        assert xml_tree.attrib, response.text

    r_del = requests.delete(rest_url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
    assert r_del.status_code >= 400, (r_del.text, rest_url)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_wms_layer(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    style = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['style_type']
    style_file_type = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('style_file_type')
    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, process_client.LAYER_TYPE, publication)
    expected_style_file = f'/layman_data_test/layers/{uuid}/input_style/{uuid}'
    expected_qgis_file = f'/qgis/data/test/layers/{uuid}/{uuid}.qgis'
    wms_layername = names.get_layer_names_by_source(uuid=uuid, ).wms
    wms_stores_url = urljoin(GS_REST_WORKSPACES, f'{wms_layername.workspace}/wmsstores/')
    wms_layers_url = urljoin(GS_REST_WORKSPACES, f'{wms_layername.workspace}/wmslayers/')

    if style_file_type:
        assert (os.path.exists(expected_style_file + '.qml')) == (style_file_type == 'qml')
        assert (os.path.exists(expected_style_file + '.sld')) == (style_file_type == 'sld')
    assert (os.path.exists(expected_qgis_file)) == (style == 'qml')

    response = requests.get(wms_stores_url,
                            auth=settings.LAYMAN_GS_AUTH,
                            timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                            )
    assert response.status_code == 200, response.json()
    if style == 'qml':
        wms_stores = [store['name'] for store in response.json()['wmsStores']['wmsStore']]
        assert f'{DEFAULT_WMS_QGIS_STORE_PREFIX}_{uuid}' in wms_stores, response.json()
    elif style == 'sld':
        url = urljoin(GS_REST, f'workspaces/{wms_layername.workspace}/styles/{uuid}')

        response = requests.get(url,
                                auth=GS_AUTH,
                                headers=headers_sld,
                                timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                                )
        response.raise_for_status()

    response = requests.get(wms_layers_url,
                            auth=settings.LAYMAN_GS_AUTH,
                            timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                            )
    assert response.status_code == 200, response.json()
    if style == 'qml':
        wms_layers = [layer['name'] for layer in response.json()['wmsLayers']['wmsLayer']]
        assert wms_layername.name in wms_layers, response.json()

    get_map = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('get_map')
    if get_map:
        url_detail, expected_file, pixel_tolerance = get_map
        url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{wms_layername.workspace}/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&FORMAT=image/png&TRANSPARENT=true&STYLES=&LAYERS={wms_layername.workspace}:{wms_layername.name}&" + url_detail
        obtained_file = f'tmp/artifacts/test_sld_style_applied_in_wms_{wms_layername.name}.png'

        assert_util.assert_same_images(url, obtained_file, expected_file, pixel_tolerance)

    authn_headers = data.HEADERS.get(data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])
    for service_endpoint in ('ows', 'wms'):
        wms_url = geoserver_client.get_wms_url(wms_layername.workspace, service_endpoint)

        layer_info = process_client.get_workspace_layer(workspace, publication, headers=authn_headers)
        crs = layer_info['native_crs']
        bbox = bbox_util.get_bbox_to_publish(layer_info['bounding_box'], crs)
        tn_bbox = gs_util.get_square_bbox(bbox)

        response = gs_util.get_layer_thumbnail(wms_url, wms_layername.name, tn_bbox, crs_def.EPSG_3857, headers=authn_headers, wms_version=VERSION)
        response.raise_for_status()
        assert 'image' in response.headers['content-type'], f'response.headers={response.headers}, response.content={response.content}'

    all_auth_info = util.get_users_and_headers_for_publication(workspace, publ_type, publication)
    headers_list_in = all_auth_info['read'][util.KEY_AUTH][util.KEY_HEADERS]
    headers_list_out = all_auth_info['read'][util.KEY_NOT_AUTH][util.KEY_HEADERS]

    for in_headers in headers_list_in:
        wms = geoserver_client.get_wms_capabilities(wms_layername.workspace, headers=in_headers)
        assert wms_layername.name in set(wms.contents)

    for out_headers in headers_list_out:
        wms = geoserver_client.get_wms_capabilities(wms_layername.workspace, headers=out_headers)
        assert wms_layername.name not in set(wms.contents)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_QML_LAYERS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_fill_project_template(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    qgs_path = f'{settings.LAYMAN_QGIS_DATA_DIR}/{publication}.qgs'
    wms_url = f'{settings.LAYMAN_QGIS_URL}?MAP={qgs_path}'
    wms_version = '1.3.0'

    with app.app_context():
        layer = Layer(layer_tuple=(workspace, publication))
    table_name = layer.table_uri.table

    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        WebMapService(wms_url, version=wms_version)
    assert excinfo.value.response.status_code == 500

    with app.app_context():
        real_bbox = layer_db.get_bbox(workspace, table_name)
        layer_crs = layer_db.get_table_crs(workspace, table_name, use_internal_srid=True)
    layer_bbox = bbox_util.get_bbox_to_publish(real_bbox, layer_crs)
    with app.app_context():
        qml_path = qgis_util.get_original_style_path(layer.uuid)
    parser = ET.XMLParser(remove_blank_text=True)
    qml_xml = ET.parse(qml_path, parser=parser)
    exp_min_scale = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('min_scale')
    if exp_min_scale is not None:
        assert qml_xml.getroot().attrib['minScale'] == exp_min_scale
    with app.app_context():
        db_types = layer_db.get_geometry_types(workspace, table_name)
        db_cols = [
            col for col in layer_db.get_all_column_infos(workspace, table_name)
            if col.name not in ['wkb_geometry', 'ogc_fid']
        ]
    qml_geometry = qgis_util.get_geometry_from_qml_and_db_types(qml_xml, db_types)
    source_type = qgis_util.get_source_type(db_types, qml_geometry)
    with app.app_context():
        column_srid = layer_db.get_column_srid(layer.table_uri.schema, layer.table_uri.table, layer.table_uri.geo_column)
    with app.app_context():
        layer_qml_str = qgis_util.fill_layer_template(layer.qgis_names.name, layer.qgis_names.id, layer_bbox,
                                                      layer_crs, qml_xml,
                                                      source_type, db_cols, layer.table_uri, column_srid, db_types)
    layer_qml = ET.fromstring(layer_qml_str.encode('utf-8'), parser=parser)
    if exp_min_scale is not None:
        assert layer_qml.attrib['minScale'] == exp_min_scale
    with app.app_context():
        qgs_str = qgis_util.fill_project_template(layer.qgis_names.name, layer.qgis_names.id, layer_qml_str, layer_crs,
                                                  settings.LAYMAN_OUTPUT_SRS_LIST, layer_bbox, source_type, layer.table_uri,
                                                  column_srid)
    with open(qgs_path, "w", encoding="utf-8") as qgs_file:
        print(qgs_str, file=qgs_file)

    wmsi = WebMapService(wms_url, version=wms_version)
    assert layer.qgis_names.name in wmsi.contents
    wms_layer = wmsi.contents[layer.qgis_names.name]
    exp_output_srs = set(settings.LAYMAN_OUTPUT_SRS_LIST)
    assert exp_output_srs.issubset(set(wms_layer.crsOptions))
    wms_layer_bbox = next((tuple(bbox_crs[:4]) for bbox_crs in wms_layer.crs_list if bbox_crs[4] == layer_crs))

    # There is probably an issue with QGIS Server 3.40.2. When publishing one-point vector layer,
    # QGIS shows bbox in GetCapabilities to be the whole world, ignoring extent mentioned in qgs file.
    # This is actually no real problem, because we are using this bbox only in this test.
    # In production, bbox from GeoServer Capabilities is the one that matters, and it is correct.
    # But because this test checks QGIS bbox, it fails with one-point layer.
    # So lets dirty fix it by not making the check for one-point layers.
    if publication not in ['post_strange_attributes_qml']:
        assert_util.assert_same_bboxes(wms_layer_bbox, layer_bbox, 0.1)

    os.remove(qgs_path)

    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        WebMapService(wms_url, version=wms_version)
    assert excinfo.value.response.status_code == 500


@pytest.mark.parametrize('workspace, publ_type, publication', [(wspace, ptype, pub)
                                                               for wspace, ptype, pub in data.LIST_LAYERS
                                                               if data.PUBLICATIONS[(wspace, ptype, pub)][data.TEST_DATA].get('micka_xml')])
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_micka_xml(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    # assert metadata file is the same as filled template except for UUID
    with app.app_context():
        template_path, prop_values = csw.get_template_path_and_values(workspace, publication, http_method='post')
    xml_file_object = micka_common_util.fill_xml_template_as_pretty_file_object(template_path, prop_values,
                                                                                csw.METADATA_PROPERTIES)
    micka_xml_def = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['micka_xml']
    expected_path = micka_xml_def['filled_template']
    with open(expected_path, encoding="utf-8") as file:
        expected_lines = file.readlines()
    exp_diff_lines = micka_xml_def['diff_lines']
    diff_lines = list(difflib.unified_diff([line.decode('utf-8') for line in xml_file_object.readlines()], expected_lines))
    plus_lines = [line for line in diff_lines if line.startswith('+ ')]
    assert len(plus_lines) == len(exp_diff_lines), ''.join(diff_lines)
    minus_lines = [line for line in diff_lines if line.startswith('- ')]
    assert len(minus_lines) == len(exp_diff_lines), ''.join(diff_lines)
    for idx, diff_line in enumerate(exp_diff_lines):
        plus_line = plus_lines[idx]
        minus_line = minus_lines[idx]
        assert plus_line == diff_line['plus_line'], f'diff_lines={"".join(diff_lines)}, idx={idx}, diff_line={diff_line}'
        assert minus_line.startswith(diff_line['minus_line_starts_with']), f'diff_lines={"".join(diff_lines)}, idx={idx}, diff_line={diff_line}'
        assert minus_line.endswith(diff_line['minus_line_ends_with']), f'diff_lines={"".join(diff_lines)}, idx={idx}, diff_line={diff_line}'

    assert len(diff_lines) == micka_xml_def['diff_lines_len'], ''.join(diff_lines)


@pytest.mark.parametrize('workspace, publ_type, publication', [
    publ_tuple for publ_tuple in data.LIST_LAYERS
    if data.PUBLICATIONS[publ_tuple][data.TEST_DATA].get('attributes') is not None
])
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_layer_attributes_in_db(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    generated_names = {'wkb_geometry', 'ogc_fid'}
    expected_names = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['attributes']
    expected_names.update(generated_names)

    with app.app_context():
        table_name = layer_db.get_internal_table_name(workspace, publication)
        attr_names = {col.name for col in layer_db.get_all_column_infos(workspace, table_name)}
    assert attr_names == expected_names
