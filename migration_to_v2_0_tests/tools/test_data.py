from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Set

import layman_settings as settings
from .client import LAYER_TYPE, MAP_TYPE

USER_1 = 'test_migrate_2_user_1'

USERS = [
    USER_1,
]

WORKSPACE_BROWSER = 'test_migrate_2_browser'

PUBLIC_WORKSPACES = [
    WORKSPACE_BROWSER,
]

WORKSPACES = USERS + PUBLIC_WORKSPACES

DEFAULT_THUMBNAIL_PIXEL_DIFF_LIMIT = 10


@dataclass
class Publication4Test:
    type: str
    workspace: str
    name: str
    owner: str
    rest_args: dict
    uuid = None
    exp_input_files: Set[str]
    exp_thumbnail_path: str | None = None


LAYER_VECTOR_SLD = Publication4Test(type=LAYER_TYPE,
                                    workspace=USER_1,
                                    name='test_vector_layer_sld',
                                    owner=USER_1,
                                    rest_args={
                                        'description': 'Description of test_vector_layer_sld',
                                    },
                                    exp_input_files={'$uuid.geojson'},
                                    exp_thumbnail_path='sample/style/basic_sld.png',
                                    )

LAYER_VECTOR_QML = Publication4Test(type=LAYER_TYPE,
                                    workspace=USER_1,
                                    name='test_vector_qml_layer',
                                    owner=USER_1,
                                    rest_args={
                                        'style_file': 'sample/style/small_layer.qml',
                                        'description': 'Description of test_vector_qml_layer',
                                    },
                                    exp_input_files={'$uuid.geojson'},
                                    exp_thumbnail_path='sample/style/small_layer_qml.png',
                                    )

LAYER_RASTER_SLD = Publication4Test(type=LAYER_TYPE,
                                    workspace=USER_1,
                                    name='test_raster_layer',
                                    owner=USER_1,
                                    rest_args={
                                        'file_paths': [
                                            'sample/layman.layer/sample_tif_tfw_rgba_opaque.tfw',
                                            'sample/layman.layer/sample_tif_tfw_rgba_opaque.tif',
                                        ],
                                        'description': 'Description of test_raster_layer',
                                    },
                                    exp_input_files={'$uuid.tfw', '$uuid.tif', '$uuid.tif.aux.xml'},
                                    exp_thumbnail_path='test_tools/data/thumbnail/raster_layer_tiff.png',
                                    )

LAYER_RASTER_SLD_JPG = Publication4Test(type=LAYER_TYPE,
                                        workspace=USER_1,
                                        name='test_raster_jpg_layer',
                                        owner=USER_1,
                                        rest_args={
                                            'file_paths': [
                                                'sample/layman.layer/sample_jpg_aux_rgb.jpg',
                                                'sample/layman.layer/sample_jpg_aux_rgb.jpg.aux.xml',
                                            ],
                                            'description': 'Description of test_raster_layer',
                                        },
                                        exp_input_files={'$uuid.jpg', '$uuid.jpg.aux.xml'},
                                        exp_thumbnail_path='test_tools/data/thumbnail/raster_layer_jpg_rgb.png',
                                        )

LAYER_RASTER_TIMESERIES = Publication4Test(type=LAYER_TYPE,
                                           workspace=WORKSPACE_BROWSER,
                                           name='test_raster_timeseries_layer',
                                           owner=settings.ANONYM_USER,
                                           rest_args={
                                               'file_paths': [
                                                   'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                                                   'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF',
                                               ],
                                               'time_regex': r'[0-9]{8}',
                                               'description': 'Description of test_raster_timeseries_layer',
                                           },
                                           exp_input_files={'S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif', 'S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF'},
                                           exp_thumbnail_path='tests/dynamic_data/publications/layer_timeseries/thumbnail_timeseries.png',
                                           )

LAYER_RASTER_ZIPPED_TIMESERIES_BY_CHUNKS = Publication4Test(type=LAYER_TYPE,
                                                            workspace=WORKSPACE_BROWSER,
                                                            name='test_raster_zipped_timeseries_by_chunks_layer',
                                                            owner=settings.ANONYM_USER,
                                                            rest_args={
                                                                'file_paths': [
                                                                    'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220316T100031_N0400_R122_T33UWR_20220316T134748_TCI_10m.tif',
                                                                    'tests/dynamic_data/publications/layer_timeseries/timeseries_tif/S2A_MSIL2A_20220319T100731_N0400_R022_T33UWR_20220319T131812_TCI_10m.TIF',
                                                                ],
                                                                'time_regex': r'[0-9]{8}',
                                                                'description': 'Description of test_raster_timeseries_layer',
                                                                'compress': True,
                                                                'with_chunks': True,
                                                            },
                                                            exp_input_files={'$uuid.zip'},
                                                            exp_thumbnail_path='tests/dynamic_data/publications/layer_timeseries/thumbnail_timeseries.png',
                                                            )

INCOMPLETE_LAYER_VECTOR_SLD = Publication4Test(type=LAYER_TYPE,
                                               workspace=USER_1,
                                               name='incomplete_test_vector_layer_sld',
                                               owner=USER_1,
                                               rest_args={
                                                   'description': 'Description of incomplete_test_vector_layer_sld',
                                               },
                                               exp_input_files=set(),
                                               )

MAP_1 = Publication4Test(type=MAP_TYPE,
                         workspace=USER_1,
                         name='test_map_1',
                         owner=USER_1,
                         rest_args={
                             'description': 'Description of test_map_1',
                         },
                         exp_input_files={'$uuid.json'},
                         )

LAYERS_TO_MIGRATE = [
    LAYER_VECTOR_SLD,
    LAYER_VECTOR_QML,
    LAYER_RASTER_SLD,
    LAYER_RASTER_SLD_JPG,
    LAYER_RASTER_TIMESERIES,
    LAYER_RASTER_ZIPPED_TIMESERIES_BY_CHUNKS,
]

MAPS_TO_MIGRATE = [
    MAP_1,
]

PUBLICATIONS_TO_MIGRATE = LAYERS_TO_MIGRATE + MAPS_TO_MIGRATE

INCOMPLETE_LAYERS = [
    INCOMPLETE_LAYER_VECTOR_SLD,
]

PUBLICATIONS = PUBLICATIONS_TO_MIGRATE + INCOMPLETE_LAYERS

UUID_FILE_PATH = 'tmp/migration_to_v2_0_tests/uuids.json'
CREATED_AT_FILE_PATH = 'tmp/migration_to_v2_0_tests/created_at.json'


def import_publication_uuids():
    with open(UUID_FILE_PATH, encoding='utf-8') as uuid_file:
        publ_uuids = json.load(uuid_file)
    assert len(publ_uuids) == len(PUBLICATIONS)
    for publ_type, workspace, name, publ_uuid in publ_uuids:
        publ = next(p for p in PUBLICATIONS if p.type == publ_type and p.workspace == workspace and p.name == name)
        publ.uuid = publ_uuid
