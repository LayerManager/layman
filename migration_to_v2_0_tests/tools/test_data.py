from __future__ import annotations

import json
from dataclasses import dataclass

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


@dataclass
class Publication:
    type: str
    workspace: str
    name: str
    owner: str
    rest_args: dict
    uuid = None
    exp_thumbnail_path: str | None = None


LAYER_VECTOR_SLD = Publication(type=LAYER_TYPE,
                               workspace=USER_1,
                               name='test_vector_layer_sld',
                               owner=USER_1,
                               rest_args={
                                   'description': 'Description of test_vector_layer_sld',
                               },
                               exp_thumbnail_path='sample/style/basic_sld.png',
                               )

LAYER_VECTOR_QML = Publication(type=LAYER_TYPE,
                               workspace=USER_1,
                               name='test_vector_qml_layer',
                               owner=USER_1,
                               rest_args={
                                   'style_file': 'sample/style/small_layer.qml',
                                   'description': 'Description of test_vector_qml_layer',
                               },
                               exp_thumbnail_path='sample/style/small_layer_qml.png',
                               )

LAYER_RASTER_SLD = Publication(type=LAYER_TYPE,
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
                               exp_thumbnail_path='test_tools/data/thumbnail/raster_layer_tiff.png',
                               )

LAYER_RASTER_TIMESERIES = Publication(type=LAYER_TYPE,
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
                                      exp_thumbnail_path='tests/dynamic_data/publications/layer_timeseries/thumbnail_timeseries.png',
                                      )

INCOMPLETE_LAYER_VECTOR_SLD = Publication(type=LAYER_TYPE,
                                          workspace=USER_1,
                                          name='incomplete_test_vector_layer_sld',
                                          owner=USER_1,
                                          rest_args={
                                              'description': 'Description of incomplete_test_vector_layer_sld',
                                          },
                                          )

MAP_1 = Publication(type=MAP_TYPE,
                    workspace=USER_1,
                    name='test_map_1',
                    owner=USER_1,
                    rest_args={
                        'description': 'Description of test_map_1',
                    },
                    )

LAYERS_TO_MIGRATE = [
    LAYER_VECTOR_SLD,
    LAYER_VECTOR_QML,
    LAYER_RASTER_SLD,
    LAYER_RASTER_TIMESERIES,
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


def import_publication_uuids():
    with open(UUID_FILE_PATH, encoding='utf-8') as uuid_file:
        publ_uuids = json.load(uuid_file)
    assert len(publ_uuids) == len(PUBLICATIONS)
    for publ_type, workspace, name, publ_uuid in publ_uuids:
        publ = next(p for p in PUBLICATIONS if p.type == publ_type and p.workspace == workspace and p.name == name)
        publ.uuid = publ_uuid
