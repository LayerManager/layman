import math
import os

import crs as crs_def
from test_tools import process_client
from tests.dynamic_data import base_test
from tests.dynamic_data.base_test_classes import Parametrization, RestArgs, RestMethod, WithChunksDomain, CompressDomain
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import util as assert_util
from tests.asserts.final.publication.geoserver import feature_spatial_precision, wms_spatial_precision, wfs_bbox, \
    wms_geographic_bbox, wms_bbox
from tests.asserts.final.publication.internal import correct_values_in_detail, thumbnail_equals, point_coordinates, \
    detail_3857bbox_value
from tests.asserts.processing.response import valid_post

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests


class StyleFileDomain(base_test.StyleFileDomainBase):
    SLD = ((f'{DIRECTORY}/sample_point_cz.sld', 'sld'), 'sld')
    QML = ((f'{DIRECTORY}/sample_point_cz.qml', 'qml'), 'qml')


TEST_CASES = {
    crs_def.EPSG_4326: {
        'exp_publication_detail': {
            'native_bounding_box': [16.6066275955110711, 49.1989353676069285, 16.6068125589999127,
                                    49.1990477233154735],
        },
        'sld': {
            'thumbnail_tolerance': 159,
        },
        'mandatory_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE, StyleFileDomain]),
        },
        'optional_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.TRUE, StyleFileDomain]),
            frozenset([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.FALSE, StyleFileDomain]),
            frozenset([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.TRUE, StyleFileDomain]),
            frozenset([RestMethod.PATCH, WithChunksDomain, CompressDomain, StyleFileDomain]),
        },
    },
    crs_def.EPSG_3857: {
        'exp_publication_detail': {
            'native_bounding_box': [1848641.3277258177, 6308684.223766193, 1848661.9177672109, 6308703.364768417],
        },
        'sld': {
            'thumbnail_tolerance': 358,
        },
        'mandatory_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE, StyleFileDomain]),
        },
        'optional_cases': {},
    },
    crs_def.EPSG_5514: {
        'exp_publication_detail': {
            'native_bounding_box': [-598214.7290553625207394, -1160319.8064114262815565, -598200.9321668159682304,
                                    -1160307.4425631782505661],
            'bounding_box': [1848640.4769060146, 6308683.577507495, 1848663.461145939, 6308704.681240051],
        },
        'sld': {
            'thumbnail_tolerance': 255,
        },
        'mandatory_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE, StyleFileDomain]),
        },
        'optional_cases': {},
    },
    crs_def.EPSG_32633: {
        'exp_publication_detail': {
            'native_bounding_box': [617041.7249990371, 5450813.311883376, 617055.1207238155, 5450825.813110342],
            'bounding_box': [1848641.1346210986, 6308683.9454576615, 1848662.0013466848, 6308703.5310932305]
        },
        'sld': {
            'thumbnail_tolerance': 379,
        },
        'mandatory_cases': {},
        'optional_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE, StyleFileDomain])
        },
    },
    crs_def.EPSG_32634: {
        'exp_publication_detail': {
            'native_bounding_box': [179985.4523066559922881, 5458866.6349301775917411, 179999.1353933966602199,
                                    5458879.0886732628569007],
            'bounding_box': [1848640.784753341, 6308683.836580554, 1848662.7351645508, 6308704.081036061]
        },
        'sld': {
            'thumbnail_tolerance': 296,
        },
        'mandatory_cases': {},
        'optional_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE, StyleFileDomain])
        },
    },
    crs_def.EPSG_3034: {
        'exp_publication_detail': {
            'native_bounding_box': [4464506.1421598251909018, 2519866.8009202978573740, 4464518.7942008553072810,
                                    2519878.8700591023080051],
            'bounding_box': [1848640.5623333207, 6308683.148403931, 1848662.1915096296, 6308704.001720284]
        },
        'sld': {
            'thumbnail_tolerance': 220,
        },
        'qml': {
            'thumbnail_tolerance': 310,
        },
        'mandatory_cases': {},
        'optional_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE, StyleFileDomain])
        },
    },
    crs_def.EPSG_3035: {
        'exp_publication_detail': {
            'native_bounding_box': [4801864.984034311, 2920036.6864006906, 4801878.080408361,
                                    2920049.1861927817],
            'bounding_box': [1848640.5726391396, 6308683.141668934, 1848662.1874939075, 6308704.004922842]
        },
        'sld': {
            'thumbnail_tolerance': 305,
        },
        'mandatory_cases': {},
        'optional_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE, StyleFileDomain])
        },
    },

}


EXP_BBOXES = {
    crs_def.EPSG_3857: {
        'bbox': [1848641.3277258177, 6308684.223766193, 1848661.9177672109, 6308703.364768417],
        'precision': 2,
    },
    crs_def.EPSG_4326: {
        'bbox': [16.6066275955110711, 49.1989353676069285, 16.6068125589999127, 49.1990477233154735],
        'precision': 0.00002,  # This is about 2 meters
    },
    crs_def.CRS_84: {
        'bbox': [16.6066275955110711, 49.1989353676069285, 16.6068125589999127, 49.1990477233154735],
        'precision': 0.00002,  # This is about 2 meters
    },
    crs_def.EPSG_5514: {
        'bbox': [-598214.7290553625207394, -1160319.8064114262815565, -598200.9321668159682304, -1160307.4425631782505661],
        'precision': 2,
    },
}


# expected coordinates manually copied from QGIS 3.16.2 in given EPSG
# point_id 1: northernmost vertex of fountain at Moravske namesti, Brno
EXP_POINT_COORDINATES = [
    (1, crs_def.EPSG_3857, (1848649.486, 6308703.297), 0.2),
    # ~5 meters! By default, GeoServer limits WFS output to 4 decimal places, about 10 m accuracy
    (1, crs_def.EPSG_4326, (16.60669976, 49.19904767), 0.00005),
    (1, crs_def.CRS_84, (16.60669976, 49.19904767), 0.00005),
    (1, crs_def.EPSG_32633, (617046.8503, 5450825.7990), 0.1),
    (1, crs_def.EPSG_32634, (179991.0748, 5458879.0878), 0.1),
    (1, crs_def.EPSG_5514, (-598208.8093, -1160307.4484), 0.1),
    (1, crs_def.EPSG_3034, (4464510.640810357, 2519878.8700591023), 0.1),
    (1, crs_def.EPSG_3035, (4801869.646727926, 2920049.1861927817), 0.1),
]

EXP_POINT_COORDINATES_GS_FIXES = {
    # Should be the same as for EPSG:4326, but for (so far) unknown reasons, wrong by about 300 m for data in EPSG:5514
    (crs_def.EPSG_5514, crs_def.CRS_84, 1): (16.6041, 49.1999)
}

EXP_POINT_COORDINATES_DB_FIXES = {
    (crs_def.EPSG_5514, crs_def.EPSG_3034, 1): (4464511.541476852, 2519881.9274773938),
    (crs_def.EPSG_5514, crs_def.EPSG_3035, 1): (4801870.58233825, 2920052.353109576),
    (crs_def.EPSG_3034, crs_def.EPSG_5514, 1): (-598210.3483076858, -1160310.3629643407),
    (crs_def.EPSG_3035, crs_def.EPSG_5514, 1): (-598210.3483076858, -1160310.3629643407),
}


EXP_WMS_PICTURES = [
    (crs_def.EPSG_3857, (1848629.922, 6308682.319, 1848674.659, 6308704.687), (601, 301), '1.3.0', 2),
    (crs_def.EPSG_4326, (49.198905759, 16.606580653, 49.199074214, 16.606874005), (560, 321), '1.3.0', 2),
    (crs_def.CRS_84, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), '1.3.0', 2),
    (crs_def.EPSG_5514, (-598222.071, -1160322.246, -598192.491, -1160305.260), (559, 321), '1.3.0', 2),
    (crs_def.EPSG_32633, (617036.812, 5450809.904, 617060.659, 5450828.394), (414, 321), '1.3.0', 2),
    (crs_def.EPSG_32634, (179980.621, 5458862.472, 180005.430, 5458881.708), (415, 321), '1.3.0', 2),
    (crs_def.EPSG_4326, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), '1.1.1', 2),
    (crs_def.CRS_84, (16.606580653, 49.198905759, 16.606874005, 49.199074214), (560, 321), '1.1.1', 2),
]

EXP_WMS_PICTURES_QGIS_FIXES = {
    # Tuples of (output CRS, source data CRS).
    # WMS GetMap of QGIS server is shifted about 3.2 meters in these cases.
    # This is probably bug in QGIS Server, and we are not able to fix it.
    # But we still want to check that the precision error is constant, so we use different expected images in such cases.
    (crs_def.CRS_84, crs_def.EPSG_5514),
    (crs_def.EPSG_3857, crs_def.EPSG_5514),
    (crs_def.EPSG_4326, crs_def.EPSG_5514),
    (crs_def.EPSG_32633, crs_def.EPSG_5514),
    (crs_def.EPSG_32634, crs_def.EPSG_5514),
    (crs_def.EPSG_5514, crs_def.EPSG_3857),
    (crs_def.EPSG_5514, crs_def.EPSG_4326),
    (crs_def.EPSG_5514, crs_def.EPSG_32633),
    (crs_def.EPSG_5514, crs_def.EPSG_32634),
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_ws_crs_vector_precision'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
        base_test.RestMethod,
        RestArgs.WITH_CHUNKS,
        RestArgs.COMPRESS,
        StyleFileDomain,
    ]

    test_cases = [base_test.TestCaseType(
        key=key,
        type=EnumTestTypes.IGNORE,
        rest_args={
            'file_paths': [file_path for file_path in [f"{DIRECTORY}/sample_point_cz_{key.split(':')[1]}.{ext}"
                                                       for ext in ['shp', 'dbf', 'prj', 'shx', 'cpg']]
                           if os.path.exists(file_path)],
        },
        params=value,
        specific_types={
            **{
                case: EnumTestTypes.OPTIONAL
                for case in value['optional_cases']
            },
            **{
                case: EnumTestTypes.MANDATORY
                for case in value['mandatory_cases']
            },
        },
    ) for key, value in TEST_CASES.items()]

    @staticmethod
    def test_precision(key: str, layer: Publication, params, rest_method, rest_args, parametrization: Parametrization):
        """Parametrized using pytest_generate_tests"""
        crs_id = key
        epsg_code = crs_id.split(':')[1]
        style_type = parametrization.style_file.style_type
        is_compressed = parametrization.rest_arg_dict[RestArgs.COMPRESS].raw_value

        # publish layer
        response = rest_method.fn(layer, args=rest_args)

        # basic checks
        valid_post(layer.workspace, layer.type, layer.name, response)
        assert_util.is_publication_valid_and_complete(layer)
        correct_values_in_detail(layer.workspace, layer.type, layer.name,
                                 exp_publication_detail={
                                     'bounding_box': EXP_BBOXES[crs_def.EPSG_3857]['bbox'],
                                     'native_crs': crs_id,
                                     **params['exp_publication_detail'],
                                 },
                                 file_extension=f'zip/sample_point_cz_{epsg_code}.shp' if is_compressed else 'shp',
                                 gdal_prefix='/vsizip/' if is_compressed else '',
                                 publ_type_detail=('vector', style_type),
                                 )

        # WFS and DB spatial precision
        for feature_id, out_crs, exp_coordinates, precision in EXP_POINT_COORDINATES:
            feature_spatial_precision(layer.workspace, layer.type, layer.name, feature_id=feature_id, crs=out_crs,
                                      exp_coordinates=EXP_POINT_COORDINATES_GS_FIXES.get((crs_id, out_crs, feature_id),
                                                                                         exp_coordinates),
                                      precision=precision,
                                      )

            if out_crs != crs_def.CRS_84:
                point_coordinates(layer.workspace, layer.type, layer.name, point_id=feature_id, crs=out_crs,
                                  exp_coordinates=EXP_POINT_COORDINATES_DB_FIXES.get((crs_id, out_crs, feature_id),
                                                                                     exp_coordinates),
                                  precision=precision,
                                  )

        # bbox spatial precision
        detail_3857bbox_value(layer.workspace, layer.type, layer.name, exp_bbox=EXP_BBOXES[crs_def.EPSG_3857]['bbox'],
                              precision=EXP_BBOXES[crs_def.EPSG_3857]['precision'],)
        wfs_bbox(layer.workspace, layer.type, layer.name, exp_bbox=EXP_BBOXES[crs_def.CRS_84]['bbox'],
                 precision=EXP_BBOXES[crs_def.CRS_84]['precision'])
        wms_geographic_bbox(layer.workspace, layer.type, layer.name, exp_bbox=EXP_BBOXES[crs_def.CRS_84]['bbox'],
                            precision=EXP_BBOXES[crs_def.CRS_84]['precision'])
        for crs, exp_bbox in EXP_BBOXES.items():
            wms_bbox(layer.workspace, layer.type, layer.name, crs=crs, exp_bbox=exp_bbox['bbox'],
                     precision=exp_bbox['precision'])

        # WMS spatial precision
        circle_diameter = 30  # according to input SLD/QML style
        num_circles = 5  # according to input SHP
        circle_perimeter = circle_diameter * math.pi
        for out_crs, extent, img_size, wms_version, diff_line_width in EXP_WMS_PICTURES:
            out_crs_code = out_crs.split(':')[1]
            pixel_diff_limit = math.ceil(circle_perimeter * diff_line_width * num_circles)
            if style_type == 'qml' and (out_crs, crs_id) in EXP_WMS_PICTURES_QGIS_FIXES:
                exp_img_suffix = f'_bad_qml_src_{epsg_code}'
            else:
                exp_img_suffix = '_ok'
            wms_spatial_precision(layer.workspace, layer.type, layer.name, wms_version=wms_version,
                                  crs=out_crs, extent=extent, img_size=img_size,
                                  pixel_diff_limit=pixel_diff_limit,
                                  obtained_file_path=f'tmp/artifacts/test_spatial_precision_wms/sample_point_cz_{out_crs_code}_{style_type}_src_{epsg_code}.png',
                                  expected_file_path=f'{DIRECTORY}/sample_point_cz_{out_crs_code}{exp_img_suffix}.png',
                                  )

        # thumbnail spatial precision
        thumbnail_equals(layer.workspace, layer.type, layer.name,
                         exp_thumbnail=f'{DIRECTORY}/sample_point_cz_{epsg_code}_thumbnail.png',
                         max_diffs=params.get(style_type, {}).get('thumbnail_tolerance'),
                         )
