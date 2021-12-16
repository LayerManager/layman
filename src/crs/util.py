from . import CRSDefinitions


def get_wms_bbox(crs, bbox, wms_version):
    wms_version_as_list = [int(value) for value in wms_version.split('.')]
    if CRSDefinitions[crs].axes_order_east_north_in_epsg_db or wms_version_as_list < [1, 3, 0]:
        result = bbox
    else:
        result = [bbox[1], bbox[0], bbox[3], bbox[2], ]
    return result
