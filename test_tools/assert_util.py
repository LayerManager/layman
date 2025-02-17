import os
import pathlib
import requests

import crs as crs_def
from layman import app, util as layman_util, settings, names
from layman.common import bbox as bbox_util
from layman.layer.geoserver import wfs, wms
from .process_client import LAYER_TYPE, get_workspace_layer_metadata_comparison, get_source_key_from_metadata_comparison
from .util import compare_images


def assert_same_images(img_url, tmp_file_path, expected_file_path, diff_threshold):
    response = requests.get(img_url,
                            timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                            )
    response.raise_for_status()
    pathlib.Path(os.path.dirname(tmp_file_path)).mkdir(parents=True, exist_ok=True)
    with open(tmp_file_path, 'wb') as file:
        for chunk in response:
            file.write(chunk)

    diffs = compare_images(expected_file_path, tmp_file_path)

    assert diffs <= diff_threshold, f"{diffs} > {diff_threshold}, img_url={img_url}, expected_file_path={expected_file_path}"

    os.remove(tmp_file_path)


def assert_same_bboxes(bbox1, bbox2, precision):
    assert len(bbox1) == 4, (bbox1, len(bbox1))
    assert len(bbox2) == 4, (bbox2, len(bbox2))
    for i in range(0, 3):
        assert abs(bbox2[i] - bbox1[i]) <= precision, (bbox1, bbox2, precision, i)


def assert_wfs_bbox(uuid, expected_bbox, *, expected_bbox_crs='EPSG:3857'):
    gs_layername = names.get_layer_names_by_source(uuid=uuid, ).wfs
    with app.app_context():
        wfs_inst = wfs.get_wfs_proxy()
    wfs_layer = f"{gs_layername.workspace}:{gs_layername.name}"
    wfs_bbox_4326 = wfs_inst.contents[wfs_layer].boundingBoxWGS84
    with app.app_context():
        wfs_bbox = bbox_util.transform(wfs_bbox_4326, crs_from=crs_def.EPSG_4326, crs_to=expected_bbox_crs, )
    assert_same_bboxes(expected_bbox, wfs_bbox, 0.00001)


def assert_wms_bbox(uuid, expected_bbox, *, expected_bbox_crs='EPSG:3857'):
    wms_layername = names.get_layer_names_by_source(uuid=uuid, ).wms
    with app.app_context():
        wms_inst = wms.get_wms_proxy()
    wms_layer = wms_inst.contents[wms_layername.name]
    bbox = next(bbox[:4] for bbox in wms_layer.crs_list if bbox[4] == expected_bbox_crs)
    assert_same_bboxes(expected_bbox, bbox, 0.00001)

    with app.app_context():
        expected_bbox_4326 = bbox_util.transform(expected_bbox, crs_from=expected_bbox_crs, crs_to=crs_def.EPSG_4326, )
    wgs84_bboxes = [bbox[:4] for bbox in wms_layer.crs_list if bbox[4] in [crs_def.EPSG_4326, crs_def.CRS_84]]
    wgs84_bboxes.append(wms_layer.boundingBoxWGS84)
    for wgs84_bbox in wgs84_bboxes:
        assert_same_bboxes(expected_bbox_4326, wgs84_bbox, 0.00001)


def assert_all_sources_bbox(workspace, layer, *, layer_uuid, expected_bbox_3857, expected_native_bbox=None, expected_native_crs=None):
    with app.app_context():
        info = layman_util.get_publication_info(workspace, LAYER_TYPE, layer,
                                                context={'key': ['bounding_box', 'native_bounding_box', 'native_crs']})
    bbox_3857 = tuple(info['bounding_box'])
    native_bbox = tuple(info['native_bounding_box'])
    native_crs = info['native_crs']

    assert_same_bboxes(expected_bbox_3857, bbox_3857, 0.00001)
    if expected_native_bbox is not None:
        assert_same_bboxes(expected_native_bbox, native_bbox, 0)
        assert expected_native_crs == native_crs

    assert_wfs_bbox(layer_uuid, expected_bbox_3857)
    assert_wms_bbox(layer_uuid, expected_bbox_3857)
    if expected_native_bbox is not None:
        assert_wfs_bbox(layer_uuid, expected_native_bbox, expected_bbox_crs=expected_native_crs)
        assert_wms_bbox(layer_uuid, expected_native_bbox, expected_bbox_crs=expected_native_crs)

    with app.app_context():
        expected_bbox_4326 = bbox_util.transform(expected_bbox_3857, crs_from=crs_def.EPSG_3857, crs_to=crs_def.EPSG_4326, )
    md_comparison = get_workspace_layer_metadata_comparison(workspace, layer)
    csw_prefix = settings.CSW_PROXY_URL
    csw_src_key = get_source_key_from_metadata_comparison(md_comparison, csw_prefix)
    assert csw_src_key is not None
    prop_key = 'extent'
    md_props = md_comparison['metadata_properties']
    assert md_props[prop_key]['equal'] is True, md_props[prop_key]
    assert md_props[prop_key]['equal_or_null'] is True, md_props[prop_key]
    csw_bbox_4326 = tuple(md_props[prop_key]['values'][csw_src_key])
    assert_same_bboxes(expected_bbox_4326, csw_bbox_4326, 0.001)


def assert_same_values_for_keys(*, expected, tested, missing_key_is_ok=False, path=''):
    if isinstance(tested, dict) and isinstance(expected, dict):
        for key in expected:
            key_path = path + f'.{key}'
            if not missing_key_is_ok or key in tested:
                assert key in tested, f'key_path={key_path}, expected={expected}, tested={tested}'
                assert_same_values_for_keys(expected=expected[key],
                                            tested=tested[key],
                                            missing_key_is_ok=missing_key_is_ok,
                                            path=key_path)
    else:
        assert expected == tested, f'path={path}, expected={expected}, tested={tested}'
