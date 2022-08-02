import os
from urllib.parse import urljoin
import difflib
import requests
from lxml import etree as ET
from owslib.wms import WebMapService
import pytest

import crs as crs_def
from geoserver import GS_REST_WORKSPACES, GS_REST, GS_AUTH, util as gs_util
from layman import settings, app, util as layman_util
from layman.common import bbox as bbox_util, geoserver as gs_common
from layman.common.micka import util as micka_common_util
from layman.layer import util as layer_util, db as layer_db, get_layer_info_keys
from layman.layer.geoserver.wms import DEFAULT_WMS_QGIS_STORE_PREFIX, VERSION
from layman.layer.micka import csw
from layman.layer.qgis import util as qgis_util
from test_tools import process_client, assert_util, geoserver_client
from test_tools.util import url_for
from .. import util
from ... import static_data as data
from ...asserts.final.publication import geoserver as asserts_gs
from ..data import ensure_publication


headers_sld = {
    'Accept': 'application/vnd.ogc.sld+xml',
    'Content-type': 'application/xml',
}


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_info(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    wms_url = f"http://localhost:8000/geoserver/{workspace}{settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX}/ows"
    wfs_url = f"http://localhost:8000/geoserver/{workspace}/wfs"
    headers = data.HEADERS.get(data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])
    style = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['style_type']

    info = process_client.get_workspace_publication(publ_type, workspace, publication, headers=headers)
    with app.app_context():
        info_internal = layer_util.get_layer_info(workspace, publication)
        expected_style_url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=publication,
                                     internal=False)

    file_type = info_internal['file']['file_type']
    item_keys = get_layer_info_keys(file_type)

    assert set(info.keys()) == item_keys, f'info={info}'
    assert info['wms'].get('url') == wms_url, f'r_json={info}, wms_url={wms_url}'
    assert 'url' in info['wms'], f'info={info}'
    assert info.get('file', dict()).get('file_type') == data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('file_type')
    if 'wfs' in info:
        assert info['wfs'].get('url') == wfs_url, f'r_json={info}, wfs_url={wfs_url}'

    assert info_internal['_style_type'] == style, f'info_internal={info_internal}'
    assert info['style']['type'] == style, info.get('style')
    external_style_url = info['style']['url']
    assert external_style_url == expected_style_url, (info, external_style_url)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_geoserver_workspace(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    asserts_gs.workspace_wms_1_3_0_capabilities_available(workspace, )
    asserts_gs.workspace_wfs_2_0_0_capabilities_available_if_vector(workspace, publ_type, publication)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_get_layer_style(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    headers = data.HEADERS.get(data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])

    with app.app_context():
        rest_url = url_for('rest_workspace_layer_style.get', workspace=workspace, layername=publication)
    response = requests.get(rest_url, headers=headers)
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

    r_del = requests.delete(rest_url)
    assert r_del.status_code >= 400, (r_del.text, rest_url)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_wms_layer(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    style = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['style_type']
    style_file_type = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('style_file_type')
    expected_style_file = f'/layman_data_test/workspaces/{workspace}/layers/{publication}/input_style/{publication}'
    expected_qgis_file = f'/qgis/data/test/workspaces/{workspace}/layers/{publication}/{publication}.qgis'
    wms_stores_url = urljoin(GS_REST_WORKSPACES, f'{workspace}_wms/wmsstores/')
    wms_layers_url = urljoin(GS_REST_WORKSPACES, f'{workspace}_wms/wmslayers/')

    with app.app_context():
        info = layman_util.get_publication_info(workspace, publ_type, publication, context={'keys': ['wms']})

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
        assert f'{DEFAULT_WMS_QGIS_STORE_PREFIX}_{publication}' in wms_stores, response.json()
    elif style == 'sld':
        url = urljoin(GS_REST, f'workspaces/{workspace}_wms/styles/{publication}')

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
        assert publication in wms_layers, response.json()

    get_map = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('get_map')
    if get_map:
        url_detail, expected_file, pixel_tolerance = get_map
        url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{workspace}_wms/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&FORMAT=image/png&TRANSPARENT=true&STYLES=&LAYERS={workspace}:{publication}&" + url_detail
        obtained_file = f'tmp/artifacts/test_sld_style_applied_in_wms_{publication}.png'

        assert_util.assert_same_images(url, obtained_file, expected_file, pixel_tolerance)

    gs_workspace = info['_wms']['workspace']
    authn_headers = data.HEADERS.get(data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_write', [None])[0])
    for service_endpoint in {'ows', 'wms'}:
        wms_url = geoserver_client.get_wms_url(gs_workspace, service_endpoint)

        layer_info = process_client.get_workspace_layer(workspace, publication, headers=authn_headers)
        crs = layer_info['native_crs']
        raw_bbox = layer_info['bounding_box'] if not bbox_util.is_empty(layer_info['bounding_box']) \
            else crs_def.CRSDefinitions[crs].default_bbox
        bbox = bbox_util.ensure_bbox_with_area(raw_bbox, crs_def.CRSDefinitions[crs].no_area_bbox_padding)
        tn_bbox = gs_util.get_square_bbox(bbox)

        response = gs_util.get_layer_thumbnail(wms_url, publication, tn_bbox, crs_def.EPSG_3857, headers=authn_headers, wms_version=VERSION)
        response.raise_for_status()
        assert 'image' in response.headers['content-type'], f'response.headers={response.headers}, response.content={response.content}'

    all_auth_info = util.get_users_and_headers_for_publication(workspace, publ_type, publication)
    headers_list_in = all_auth_info['read'][util.KEY_AUTH][util.KEY_HEADERS]
    headers_list_out = all_auth_info['read'][util.KEY_NOT_AUTH][util.KEY_HEADERS]

    for in_headers in headers_list_in:
        wms = geoserver_client.get_wms_capabilities(gs_workspace, headers=in_headers)
        assert publication in set(wms.contents)

    for out_headers in headers_list_out:
        wms = geoserver_client.get_wms_capabilities(gs_workspace, headers=out_headers)
        assert publication not in set(wms.contents)


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_QML_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_fill_project_template(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    qgs_path = f'{settings.LAYMAN_QGIS_DATA_DIR}/{publication}.qgs'
    wms_url = f'{settings.LAYMAN_QGIS_URL}?MAP={qgs_path}'
    wms_version = '1.3.0'

    layer_info = process_client.get_workspace_publication(publ_type, workspace, publication)
    layer_uuid = layer_info['uuid']
    table_name = layer_info['db_table']['name']

    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        WebMapService(wms_url, version=wms_version)
    assert excinfo.value.response.status_code == 500

    with app.app_context():
        layer_bbox = layer_db.get_bbox(workspace, table_name)
        layer_crs = layer_db.get_crs(workspace, table_name)
    layer_bbox = layer_bbox if not bbox_util.is_empty(layer_bbox) else crs_def.CRSDefinitions[layer_crs].default_bbox
    with app.app_context():
        qml_path = qgis_util.get_original_style_path(workspace, publication)
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
    qml_geometry = qgis_util.get_qml_geometry_from_qml(qml_xml)
    source_type = qgis_util.get_source_type(db_types, qml_geometry)
    with app.app_context():
        layer_qml_str = qgis_util.fill_layer_template(workspace, publication, layer_uuid, layer_bbox, layer_crs, qml_xml, source_type, db_cols, table_name)
    layer_qml = ET.fromstring(layer_qml_str.encode('utf-8'), parser=parser)
    if exp_min_scale is not None:
        assert layer_qml.attrib['minScale'] == exp_min_scale
    with app.app_context():
        qgs_str = qgis_util.fill_project_template(workspace, publication, layer_uuid, layer_qml_str, layer_crs, settings.LAYMAN_OUTPUT_SRS_LIST,
                                                  layer_bbox, source_type, table_name)
    with open(qgs_path, "w") as qgs_file:
        print(qgs_str, file=qgs_file)

    wmsi = WebMapService(wms_url, version=wms_version)
    assert publication in wmsi.contents
    wms_layer = wmsi.contents[publication]
    exp_output_srs = set(settings.LAYMAN_OUTPUT_SRS_LIST)
    assert exp_output_srs.issubset(set(wms_layer.crsOptions))
    wms_layer_bbox = next((tuple(bbox_crs[:4]) for bbox_crs in wms_layer.crs_list if bbox_crs[4] == layer_crs))
    assert_util.assert_same_bboxes(wms_layer_bbox, layer_bbox, 0.1)

    os.remove(qgs_path)

    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        WebMapService(wms_url, version=wms_version)
    assert excinfo.value.response.status_code == 500


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_LAYERS)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_gs_data_security(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    auth = settings.LAYMAN_GS_AUTH
    is_personal_workspace = workspace in data.USERS
    owner_and_everyone_roles = gs_common.layman_users_to_geoserver_roles({workspace, settings.RIGHTS_EVERYONE_ROLE})
    owner_role_set = gs_common.layman_users_to_geoserver_roles({workspace})
    with app.app_context():
        info = layman_util.get_publication_info(workspace, publ_type, publication, context={'keys': ['access_rights', 'wms']})
    expected_roles = info['access_rights']
    gs_workspace = info['_wms']['workspace']
    file_type = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('file_type')
    workspaces = [workspace, gs_workspace] if file_type != settings.FILE_TYPE_RASTER else [gs_workspace]
    for right_type in ['read', 'write']:
        for wspace in workspaces:
            gs_expected_roles = gs_common.layman_users_to_geoserver_roles(expected_roles[right_type])
            gs_roles = gs_util.get_security_roles(f'{wspace}.{publication}.{right_type[0]}', auth)
            assert gs_expected_roles == gs_roles\
                or (is_personal_workspace
                    and gs_expected_roles == owner_and_everyone_roles == gs_roles.union(owner_role_set)), f'gs_expected_roles={gs_expected_roles}, gs_roles={gs_roles}, wspace={wspace}, is_personal_workspace={is_personal_workspace}'


@pytest.mark.parametrize('workspace, publ_type, publication', [(wspace, ptype, pub)
                                                               for wspace, ptype, pub in data.LIST_LAYERS
                                                               if data.PUBLICATIONS[(wspace, ptype, pub)][data.TEST_DATA].get('micka_xml')])
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_micka_xml(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    # assert metadata file is the same as filled template except for UUID
    with app.app_context():
        template_path, prop_values = csw.get_template_path_and_values(workspace, publication, http_method='post')
    xml_file_object = micka_common_util.fill_xml_template_as_pretty_file_object(template_path, prop_values,
                                                                                csw.METADATA_PROPERTIES)
    micka_xml_def = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['micka_xml']
    expected_path = micka_xml_def['filled_template']
    with open(expected_path) as file:
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
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_layer_attributes_in_db(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)
    generated_names = {'wkb_geometry', 'ogc_fid'}
    expected_names = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['attributes']
    expected_names.update(generated_names)

    with app.app_context():
        table_name = layer_db.get_table_name(workspace, publication)
        attr_names = {col.name for col in layer_db.get_all_column_infos(workspace, table_name)}
    assert attr_names == expected_names
