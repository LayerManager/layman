from osgeo import ogr

from layman.http import LaymanError
from layman.settings import INPUT_SRS_LIST

def save_files(files, filepath_mapping, main_filename, check_crs):
    for file in files:
        if filepath_mapping[file.filename] is None:
            continue
        # logger.info('Saving file {} as {}'.format(
        #     file.filename, filepath_mapping[file.filename]))
        file.save(filepath_mapping[file.filename])

    # check feature layers in source file
    inDriver = ogr.GetDriverByName("GeoJSON")
    inDataSource = inDriver.Open(filepath_mapping[main_filename], 0)
    n_layers = inDataSource.GetLayerCount()
    if n_layers != 1:
        raise LaymanError(5, {'found': n_layers, 'expected': 1})
    feature_layer = inDataSource.GetLayerByIndex(0)

    if check_crs:
        crs = feature_layer.GetSpatialRef()
        crs_auth_name = crs.GetAuthorityName(None)
        crs_code = crs.GetAuthorityCode(None)
        crs_id = crs_auth_name+":"+crs_code
        if crs_id not in INPUT_SRS_LIST:
            raise LaymanError(4, {'found': crs_id, 'supported_values': INPUT_SRS_LIST})
        return crs_id
    else:
        return
