import os

import crs as crs_def
from test_tools import process_client
from tests.dynamic_data import base_test
from tests.dynamic_data.base_test_classes import Parametrization, RestArgs, RestMethod, WithChunksDomain, CompressDomain
from tests import EnumTestTypes, Publication4Test
from tests.asserts.final.publication import util as assert_util
from tests.asserts.final.publication.geoserver import wms_spatial_precision, wms_geographic_bbox, wms_bbox
from tests.asserts.final.publication.internal import correct_values_in_detail, thumbnail_equals, \
    detail_3857bbox_value
from tests.asserts.processing.response import valid_post

DIRECTORY = os.path.dirname(os.path.abspath(__file__))

pytest_generate_tests = base_test.pytest_generate_tests


TEST_CASES = {
    crs_def.EPSG_4326: {
        'exp_publication_detail': {
            'native_bounding_box': [16.606587576736, 49.198911725592005, 16.606851456552, 49.199072702792],
            'bounding_box': [1848636.8728561546, 6308680.196100452, 1848666.2478229022, 6308707.6202965565],
        },
        'thumbnail_tolerance': 5,
        'mandatory_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        },
        'optional_cases': {},
    },
    crs_def.EPSG_3857: {
        'exp_publication_detail': {
            'native_bounding_box': [1848636.3811272, 6308680.1143396, 1848666.8389494002, 6308707.5628834],
            'bounding_box': [1848636.3811272, 6308680.1143396, 1848666.8389494002, 6308707.5628834],
        },
        'thumbnail_tolerance': 173,
        'mandatory_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        },
        'optional_cases': {},
    },
    crs_def.EPSG_5514: {
        'exp_publication_detail': {
            'native_bounding_box': [-598217.8828349999, -1160322.4535628, -598198.2786699999, -1160305.0114542001],
            'bounding_box': [1848635.2878977319, 6308679.0262031425, 1848667.9258161425, 6308708.821095935],
        },
        'thumbnail_tolerance': 5,
        'mandatory_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        },
        'optional_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.TRUE]),
            frozenset([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.FALSE]),
            frozenset([RestMethod.POST, WithChunksDomain.TRUE, CompressDomain.TRUE]),
            frozenset([RestMethod.PATCH, WithChunksDomain, CompressDomain]),
        },
    },
    crs_def.EPSG_32633: {
        'exp_publication_detail': {
            'native_bounding_box': [617038.822659, 5450810.940462001, 617058.1279862, 5450828.1348948],
            'bounding_box': [1848636.6245464054, 6308680.214995095, 1848666.6700974994, 6308707.182104623],
        },
        'thumbnail_tolerance': 5,
        'mandatory_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        },
        'optional_cases': {},
    },
    crs_def.EPSG_32634: {
        'exp_publication_detail': {
            'native_bounding_box': [179982.9579464, 5458864.3851908, 180001.7869064, 5458881.6025756],
            'bounding_box': [1848636.761700774, 6308680.177464705, 1848666.9742205392, 6308708.157743086],
        },
        'thumbnail_tolerance': 5,
        'mandatory_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        },
        'optional_cases': {},
    },
    crs_def.EPSG_3034: {
        'exp_publication_detail': {
            'native_bounding_box': [4464503.1786742, 2519864.4423224, 4464521.7093864, 2519881.639366],
            'bounding_box': [1848635.5622696981, 6308679.010490673, 1848667.1735165308, 6308708.795145725],
        },
        'thumbnail_tolerance': 5,
        'mandatory_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        },
        'optional_cases': {},
    },
    crs_def.EPSG_3035: {
        'exp_publication_detail': {
            'native_bounding_box': [4801862.1376458, 2920034.1033083997, 4801881.1769774, 2920052.2550572],
            'bounding_box': [1848635.8928185008, 6308678.776642735, 1848667.3134760845, 6308709.076431936],
        },
        'thumbnail_tolerance': 5,
        'mandatory_cases': {
            frozenset([RestMethod.POST, WithChunksDomain.FALSE, CompressDomain.FALSE]),
        },
        'optional_cases': {},
    },
}


EXP_WMS_PICTURES = [
    (crs_def.EPSG_3857, (1848636.381, 6308680.114, 1848666.839, 6308707.563), (169, 171), '1.3.0'),
    (crs_def.EPSG_4326, (49.1989117, 16.6065876, 49.1990727, 16.6068515), (146, 100), '1.3.0'),
    (crs_def.EPSG_4326, (16.6065876, 49.1989117, 16.6068515, 49.1990727), (146, 100), '1.1.1'),
    (crs_def.CRS_84, (16.6065876, 49.1989117, 16.6068515, 49.1990727), (146, 100), '1.3.0'),
    (crs_def.CRS_84, (16.6065876, 49.1989117, 16.6068515, 49.1990727), (146, 100), '1.1.1'),
    (crs_def.EPSG_5514, (-598217.883, -1160322.454, -598198.279, -1160305.011), (161, 147), '1.3.0'),
    (crs_def.EPSG_32633, (617038.823, 5450810.940, 617058.128, 5450828.135), (148, 148), '1.3.0'),
    (crs_def.EPSG_32634, (179980.621, 5458862.472, 180005.430, 5458881.708), (150, 154), '1.3.0'),
]


EXP_BBOXES = {
    crs_def.EPSG_3857: {
        'bbox': [1848636.381, 6308680.114, 1848666.839, 6308707.563],
        'precision': 2,
    },
    crs_def.EPSG_4326: {
        'bbox': [16.6065876, 49.1989117, 16.6068515, 49.1990727],
        'precision': 0.00002,  # This is about 2 meters
    },
    crs_def.CRS_84: {
        'bbox': [16.6065876, 49.1989117, 16.6068515, 49.1990727],
        'precision': 0.00002,  # This is about 2 meters
    },
    crs_def.EPSG_5514: {
        'bbox': [-598217.883, -1160322.454, -598198.279, -1160305.011],
        'precision': 2.05,
    },
}


class TestLayer(base_test.TestSingleRestPublication):

    workspace = 'dynamic_test_ws_crs_raster_precision'

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
        base_test.RestMethod,
        RestArgs.WITH_CHUNKS,
        RestArgs.COMPRESS,
    ]

    test_cases = [base_test.TestCaseType(
        key=key,
        type=EnumTestTypes.IGNORE,
        rest_args={
            'file_paths': [f"{DIRECTORY}/cz_{key.split(':')[1]}.tif"],
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
    def test_precision(key: str, layer: Publication4Test, params, rest_method, rest_args, parametrization: Parametrization):
        """Parametrized using pytest_generate_tests"""
        crs_id = key
        epsg_code = crs_id.split(':')[1]
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
                                 file_extension=f'zip/cz_{epsg_code}.tif' if is_compressed else 'tif',
                                 gdal_prefix='/vsizip/' if is_compressed else '',
                                 publ_type_detail=('raster', 'sld'),
                                 )

        # bbox spatial precision
        detail_3857bbox_value(layer.workspace, layer.type, layer.name, exp_bbox=EXP_BBOXES[crs_def.EPSG_3857]['bbox'],
                              precision=EXP_BBOXES[crs_def.EPSG_3857]['precision'],
                              contains=False,  # because bbox of each input raster is slightly different
                              )
        wms_geographic_bbox(layer.workspace, layer.type, layer.name, exp_bbox=EXP_BBOXES[crs_def.CRS_84]['bbox'],
                            precision=EXP_BBOXES[crs_def.CRS_84]['precision'],
                            contains=False,  # because bbox of each input raster is slightly different
                            )
        for crs, exp_bbox in EXP_BBOXES.items():
            wms_bbox(layer.workspace, layer.type, layer.name, crs=crs, exp_bbox=exp_bbox['bbox'],
                     precision=exp_bbox['precision'],
                     contains=False,  # because bbox of each input raster is slightly different
                     )

        # WMS spatial precision
        for out_crs, extent, img_size, wms_version in EXP_WMS_PICTURES:
            out_crs_code = out_crs.split(':')[1]
            wms_spatial_precision(layer.workspace, layer.type, layer.name, wms_version=wms_version,
                                  crs=out_crs, extent=extent, img_size=img_size,
                                  pixel_diff_limit=0,
                                  obtained_file_path=f'tmp/artifacts/test_spatial_precision_wms/cz_raster_{epsg_code}/{out_crs_code}.png',
                                  expected_file_path=f'{DIRECTORY}/cz_{epsg_code}/{out_crs_code}.png',
                                  )

        # thumbnail spatial precision
        thumbnail_equals(layer.workspace, layer.type, layer.name,
                         exp_thumbnail=f'{DIRECTORY}/cz_{epsg_code}/thumbnail.png',
                         max_diffs=params['thumbnail_tolerance'],
                         )
