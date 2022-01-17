import math
import requests

from layman import app, settings, util as layman_util
from test_tools import util as test_util, geoserver_client, process_client, assert_util


def workspace_wms_1_3_0_capabilities_available(workspace):
    with app.app_context():
        internal_wms_url = test_util.url_for('geoserver_proxy_bp.proxy', subpath=workspace + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX + '/ows')

    r_wms = requests.get(internal_wms_url, params={
        'service': 'WMS',
        'request': 'GetCapabilities',
        'version': '1.3.0',
    })
    assert r_wms.status_code == 200


def workspace_wfs_2_0_0_capabilities_available_if_vector(workspace, publ_type, name):
    with app.app_context():
        internal_wfs_url = test_util.url_for('geoserver_proxy_bp.proxy', subpath=workspace + '/wfs')

    with app.app_context():
        file_info = layman_util.get_publication_info(workspace, publ_type, name, {'keys': ['file']})['file']
    file_type = file_info['file_type']
    if file_type == settings.FILE_TYPE_VECTOR:
        r_wfs = requests.get(internal_wfs_url, params={
            'service': 'WFS',
            'request': 'GetCapabilities',
            'version': '2.0.0',
        })
        assert r_wfs.status_code == 200


def feature_spatial_precision(workspace, publ_type, name, *, feature_id, epsg_code, exp_coordinates, precision):
    assert publ_type == process_client.LAYER_TYPE

    feature_collection = geoserver_client.get_features(workspace, name, epsg_code=epsg_code)
    feature = next(f for f in feature_collection['features'] if f['properties']['point_id'] == feature_id)
    for idx, coordinate in enumerate(feature['geometry']['coordinates']):
        assert abs(coordinate - exp_coordinates[idx]) <= precision, f"EPSG:{epsg_code}: expected coordinates={exp_coordinates}, found coordinates={feature['geometry']['coordinates']}"


def wms_spatial_precision(workspace, publ_type, name, *, epsg_code, extent, img_size, wms_version, diff_line_width, obtained_file_path,
                          expected_file_path, ):
    assert publ_type == process_client.LAYER_TYPE

    crs_name = {
        '1.1.1': 'SRS',
        '1.3.0': 'CRS',
    }[wms_version]

    url = f'http://{settings.LAYMAN_SERVER_NAME}/geoserver/{workspace}_wms/wms?SERVICE=WMS&VERSION={wms_version}&REQUEST=GetMap&FORMAT=image%2Fpng&TRANSPARENT=true&STYLES&LAYERS={workspace}_wms%3A{name}&FORMAT_OPTIONS=antialias%3Afull&{crs_name}=EPSG%3A{epsg_code}&WIDTH={img_size[0]}&HEIGHT={img_size[1]}&BBOX={"%2C".join((str(c) for c in extent))}'

    circle_diameter = 30
    circle_perimeter = circle_diameter * math.pi
    num_circles = 5
    pixel_diff_limit = circle_perimeter * num_circles * diff_line_width

    assert_util.assert_same_images(url, obtained_file_path, expected_file_path, pixel_diff_limit)
