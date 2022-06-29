import datetime
import psycopg2
from psycopg2 import tz

from layman import settings
from .util import to_safe_layer_name, fill_in_partial_info_statuses


def test_to_safe_layer_name():
    assert to_safe_layer_name('') == 'layer'
    assert to_safe_layer_name(' ?:"+  @') == 'layer'
    assert to_safe_layer_name('01 Stanice vodních toků 26.4.2017 (voda)') == '01_stanice_vodnich_toku_26_4_2017_voda'
    assert to_safe_layer_name('řecko') == 'recko'


def test_fill_in_partial_info_statuses():
    class CeleryResult:
        @staticmethod
        def failed():
            return False

        @staticmethod
        # pylint: disable=unused-argument
        def get(propagate):
            return False

        @staticmethod
        def successful():
            return False

        state = 'PENDING'

    publication_info = {'uuid': '157d0c0b-f893-4b93-bd2f-04a771822e09',
                        'id': 631,
                        'name': 'name_of_layer',
                        'title': 'Title of the layer',
                        'type': 'layman.layer',
                        'style_type': 'qml',
                        'updated_at': datetime.datetime(2021, 9, 9, 9, 39, 59, 167846,
                                                        tzinfo=tz.FixedOffsetTimezone(offset=0, name=None)),
                        'bounding_box': [1870322.81512642, 6281928.49798181, 1892002.82941466, 6304200.72172059],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [1870322.81512642, 6281928.49798181, 1892002.82941466, 6304200.72172059],
                        'access_rights': {'read': ['lay3', 'EVERYONE'], 'write': ['lay3', 'EVERYONE']},
                        'file': {'path': 'layers/name_of_layer/input_file/name_of_layer.geojson',
                                 'file_type': settings.FILE_TYPE_VECTOR},
                        'db_table': {'name': 'name_of_layer'},
                        'style': {'url': 'https://www.layman.cz/rest/workspaces/workspace_name/layers/name_of_layer/style',
                                  'type': 'qml'}}

    task_info_db_table = CeleryResult()
    task_info_prime_bbox = CeleryResult()
    task_info_qgis_wms = CeleryResult()
    task_info_gs_wfs = CeleryResult()
    task_info_gs_wms = CeleryResult()
    task_info_gs_sld = CeleryResult()
    task_info_fs_thumbnail = CeleryResult()
    task_info_micka_soap = CeleryResult()

    chain_info = {'by_name': {'layman.layer.db.table.refresh': task_info_db_table,
                              'layman.layer.prime_db_schema.bbox.refresh': task_info_prime_bbox,
                              'layman.layer.qgis.wms.refresh': task_info_qgis_wms,
                              'layman.layer.geoserver.wfs.refresh': task_info_gs_wfs,
                              'layman.layer.geoserver.wms.refresh': task_info_gs_wms,
                              'layman.layer.geoserver.sld.refresh': task_info_gs_sld,
                              'layman.layer.filesystem.thumbnail.refresh': task_info_fs_thumbnail,
                              'layman.layer.micka.soap.refresh': task_info_micka_soap,
                              },
                  'by_order': [task_info_db_table, task_info_prime_bbox, task_info_qgis_wms, task_info_gs_wfs, task_info_gs_wms,
                               task_info_gs_sld, task_info_fs_thumbnail, task_info_micka_soap, ],
                  'finished': True,
                  'state': 'FAILURE',
                  'last': task_info_micka_soap,
                  }

    expected_info = {
        'uuid': '157d0c0b-f893-4b93-bd2f-04a771822e09',
        'id': 631,
        'name': 'name_of_layer',
        'title': 'Title of the layer',
        'type': 'layman.layer',
        'style_type': 'qml',
        'updated_at': datetime.datetime(2021,
                                        9,
                                        9,
                                        9,
                                        39,
                                        59,
                                        167846,
                                        tzinfo=psycopg2.tz.FixedOffsetTimezone(offset=0,
                                                                               name=None)),
        'bounding_box': [
            1870322.81512642,
            6281928.49798181,
            1892002.82941466,
            6304200.72172059
        ],
        'native_crs': 'EPSG:3857',
        'native_bounding_box': [
            1870322.81512642,
            6281928.49798181,
            1892002.82941466,
            6304200.72172059,
        ],
        'access_rights': {
            'read': [
                'lay3',
                'EVERYONE'
            ],
            'write': [
                'lay3',
                'EVERYONE'
            ]
        },
        'file': {
            'path': 'layers/name_of_layer/input_file/name_of_layer.geojson',
            'file_type': 'vector'
        },
        'db_table': {
            'name': 'name_of_layer',
        },
        'style': {
            'url': 'https://www.layman.cz/rest/workspaces/workspace_name/layers/name_of_layer/style',
            'type': 'qml',
        },
        'wfs': {
            'status': 'NOT_AVAILABLE'
        },
        'wms': {
            'status': 'NOT_AVAILABLE'
        },
        'thumbnail': {
            'status': 'NOT_AVAILABLE'
        },
        'metadata': {
            'status': 'NOT_AVAILABLE'
        }
    }

    filled_info = fill_in_partial_info_statuses(publication_info, chain_info)
    assert filled_info == expected_info, f'filled_info={filled_info}, expected_info={expected_info}'
