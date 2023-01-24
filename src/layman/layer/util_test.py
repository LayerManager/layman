import datetime
import re
import psycopg2
from psycopg2 import tz
import pytest

from db import TableUri
from layman import settings, LaymanError
from test_tools import util as test_util, external_db
from . import util
from .util import to_safe_layer_name, fill_in_partial_info_statuses


@pytest.fixture(scope="module")
def ensure_tables():
    tables = [
        ('schema_name', 'table_name', 'geo_wkb_column'),
    ]
    for schema, table, geo_column in tables:
        external_db.ensure_table(schema, table, geo_column)

    yield

    for schema, table, _ in tables:
        external_db.drop_table(schema, table)


@pytest.mark.parametrize('unsafe_name, exp_output', [
    ('', 'layer'),
    (' ?:"+  @', 'layer'),
    ('01 Stanice vodních toků 26.4.2017 (voda)', '01_stanice_vodnich_toku_26_4_2017_voda'),
    ('řĚčKó', 'recko'),
])
def test_to_safe_layer_name(unsafe_name, exp_output):
    assert to_safe_layer_name(unsafe_name) == exp_output


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
                        '_style_type': 'qml',
                        'updated_at': datetime.datetime(2021, 9, 9, 9, 39, 59, 167846,
                                                        tzinfo=tz.FixedOffsetTimezone(offset=0, name=None)),
                        'bounding_box': [1870322.81512642, 6281928.49798181, 1892002.82941466, 6304200.72172059],
                        'native_crs': 'EPSG:3857',
                        'native_bounding_box': [1870322.81512642, 6281928.49798181, 1892002.82941466, 6304200.72172059],
                        'access_rights': {'read': ['lay3', 'EVERYONE'], 'write': ['lay3', 'EVERYONE']},
                        'file': {'path': 'layers/name_of_layer/input_file/name_of_layer.geojson',
                                 'file_type': settings.FILE_TYPE_VECTOR},
                        '_file_type': settings.FILE_TYPE_UNKNOWN,
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
                              'layman.layer.prime_db_schema.file_data.refresh': task_info_prime_bbox,
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
        '_style_type': 'qml',
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
        '_file_type': settings.FILE_TYPE_UNKNOWN,
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


@pytest.mark.usefixtures('ensure_external_db', 'ensure_tables')
@pytest.mark.parametrize('external_table_uri_str, exp_result', [
    ('postgresql://docker:docker@postgresql:5432/external_test_db?schema=schema_name&table=table_name&geo_column=geo_wkb_column&connect_timeout=10&target_session_attrs=primary', TableUri(
        db_uri_str='postgresql://docker:docker@postgresql:5432/external_test_db?connect_timeout=10&target_session_attrs=primary',
        schema='schema_name',
        table='table_name',
        geo_column='geo_wkb_column',
    )),
])
def test_parse_external_table_uri_str(external_table_uri_str, exp_result):
    result = util.parse_and_validate_external_table_uri_str(external_table_uri_str)
    assert result == exp_result


@pytest.mark.usefixtures('ensure_external_db', 'ensure_tables')
@pytest.mark.parametrize('external_table_uri_str, exp_error', [
    pytest.param('postgresql://postgresql', {
        'http_code': 400,
        'code': 2,
        'detail': {'parameter': 'db_connection',
                   'message': 'Parameter `db_connection` is expected to be valid URL with `host` part and query parameters `schema`, `table`, and `geo_column`.',
                   'expected': util.EXTERNAL_TABLE_URI_PATTERN,
                   'found': {
                       'db_connection': 'postgresql://postgresql',
                       'host': 'postgresql',
                       'schema': None,
                       'table': None,
                       'geo_column': None,
                   },
                   },
    }, id='only_scheme_host'),
    pytest.param('postgresql:///external_test_db?schema=schema_name&table=table_name&geo_column=wkb_geometry', {
        'http_code': 400,
        'code': 2,
        'detail': {'parameter': 'db_connection',
                   'message': 'Parameter `db_connection` is expected to be valid URL with `host` part and query parameters `schema`, `table`, and `geo_column`.',
                   'expected': util.EXTERNAL_TABLE_URI_PATTERN,
                   'found': {
                       'db_connection': 'postgresql:///external_test_db?schema=schema_name&table=table_name&geo_column=wkb_geometry',
                       'host': None,
                       'schema': 'schema_name',
                       'table': 'table_name',
                       'geo_column': 'wkb_geometry',
                   },
                   },
    }, id='without_netloc'),
    pytest.param('postgresql://docker:docker@:5432/external_test_db?schema=schema_name&table=table_name&geo_column=wkb_geometry', {
        'http_code': 400,
        'code': 2,
        'detail': {'parameter': 'db_connection',
                   'message': 'Parameter `db_connection` is expected to be valid URL with `host` part and query parameters `schema`, `table`, and `geo_column`.',
                   'expected': util.EXTERNAL_TABLE_URI_PATTERN,
                   'found': {
                       'db_connection': 'postgresql://docker:docker@:5432/external_test_db?schema=schema_name&table=table_name&geo_column=wkb_geometry',
                       'host': None,
                       'schema': 'schema_name',
                       'table': 'table_name',
                       'geo_column': 'wkb_geometry',
                   },
                   },
    }, id='without_hostname'),
    pytest.param('postgresql://docker:docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', {
        'http_code': 400,
        'code': 2,
        'detail': {'parameter': 'db_connection',
                   'message': 'Parameter `db_connection` is expected to be valid URL with `host` part and query parameters `schema`, `table`, and `geo_column`.',
                   'expected': util.EXTERNAL_TABLE_URI_PATTERN,
                   'found': {
                       'db_connection': 'postgresql://docker:docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry',
                       'host': 'postgresql',
                       'schema': None,
                       'table': 'table_name',
                       'geo_column': 'wkb_geometry',
                   },
                   },
    }, id='without_schema'),
    pytest.param('postgresql://docker:docker@postgresql:5432/external_test_db?schema=schema_name&geo_column=wkb_geometry', {
        'http_code': 400,
        'code': 2,
        'detail': {'parameter': 'db_connection',
                   'message': 'Parameter `db_connection` is expected to be valid URL with `host` part and query parameters `schema`, `table`, and `geo_column`.',
                   'expected': util.EXTERNAL_TABLE_URI_PATTERN,
                   'found': {
                       'db_connection': 'postgresql://docker:docker@postgresql:5432/external_test_db?schema=schema_name&geo_column=wkb_geometry',
                       'host': 'postgresql',
                       'schema': 'schema_name',
                       'table': None,
                       'geo_column': 'wkb_geometry',
                   },
                   },
    }, id='without_table'),
    pytest.param('postgresql://docker:docker@postgresql:5432/external_test_db?schema=schema_name&table=no_table_name&geo_column=wkb_geometry', {
        'http_code': 400,
        'code': 2,
        'detail': {
            'parameter': 'db_connection',
            'message': 'Table "schema_name"."no_table_name" not found in database.',
            'expected': util.EXTERNAL_TABLE_URI_PATTERN,
            'found': {
                'db_connection': 'postgresql://docker:docker@postgresql:5432/external_test_db?schema=schema_name&table=no_table_name&geo_column=wkb_geometry',
                'schema': 'schema_name',
                'table': 'no_table_name',
            },
        },
    }, id='invalid_table_name'),
    pytest.param('postgresql://docker:docker@postgresql:5432/external_test_db?schema=schema_name&table=Table_name&geo_column=wkb_geometry', {
        'http_code': 400,
        'code': 2,
        'detail': {
            'parameter': 'db_connection',
            'message': 'Table "schema_name"."Table_name" not found in database. Did you mean "schema_name"."table_name"?',
            'expected': util.EXTERNAL_TABLE_URI_PATTERN,
            'found': {
                'db_connection': 'postgresql://docker:docker@postgresql:5432/external_test_db?schema=schema_name&table=Table_name&geo_column=wkb_geometry',
                'schema': 'schema_name',
                'table': 'Table_name',
            },
        },
    }, id='table_name_with_different_case'),
    pytest.param('postgresql://docker:docker@postgresql:5432/external_test_db?schema=schema_name&table=table_name&geo_column=no_wkb_geometry', {
        'http_code': 400,
        'code': 2,
        'detail': {
            'parameter': 'db_connection',
            'message': 'Column `geo_column` not found among geometry columns.',
            'expected': util.EXTERNAL_TABLE_URI_PATTERN,
            'found': {
                'db_connection': 'postgresql://docker:docker@postgresql:5432/external_test_db?schema=schema_name&table=table_name&geo_column=no_wkb_geometry',
                'schema': 'schema_name',
                'table': 'table_name',
                'geo_column': 'no_wkb_geometry',
            },
        },
    }, id='invalid_geo_column'),
    pytest.param('postgresql://docker:docker@postgresql:5432/external_test_db?schema=no_schema&table=table_name&geo_column=no_wkb_geometry', {
        'http_code': 400,
        'code': 2,
        'detail': {
            'parameter': 'db_connection',
            'message': 'Table "no_schema"."table_name" not found in database.',
            'expected': util.EXTERNAL_TABLE_URI_PATTERN,
            'found': {
                'db_connection': 'postgresql://docker:docker@postgresql:5432/external_test_db?schema=no_schema&table=table_name&geo_column=no_wkb_geometry',
                'schema': 'no_schema',
                'table': 'table_name',
            },
        },
    }, id='invalid_schema'),
])
def test_validate_external_table_uri_str(external_table_uri_str, exp_error):
    with pytest.raises(LaymanError) as exc_info:
        util.parse_and_validate_external_table_uri_str(external_table_uri_str)
    test_util.assert_error(exp_error, exc_info)


@pytest.mark.usefixtures('ensure_external_db')
@pytest.mark.parametrize('external_table_uri_str, exp_err_msg_patterns', [
    pytest.param('postgresql://postgresql:5432/external_test_db?schema=schema_name&table=table_name&geo_column=wkb_geometry', [
        r'^connection to server at \"postgresql\" \(\d+.\d+.\d+.\d+\), port 5432 failed: fe_sendauth: no password supplied\n$',
        r'local user with ID 1000 does not exist\n',
    ], id='without_username'),
    pytest.param('postgresql://docker:docker@postgresql:5432?schema=schema_name&table=table_name&geo_column=wkb_geometry', [
        r'^connection to server at "postgresql" \(\d+.\d+.\d+.\d+\), port 5432 failed: FATAL:  database "docker" does not exist$'
    ], id='without_database'),
    pytest.param('postgresql://no_user@postgresql:5432/external_test_db?schema=schema_name&table=table_name&geo_column=wkb_geometry', [
        r'^connection to server at \"postgresql\" \(\d+.\d+.\d+.\d+\), port 5432 failed: fe_sendauth: no password supplied\n$'
    ], id='invalid_user'),
])
def test_validate_external_table_connection(external_table_uri_str, exp_err_msg_patterns):
    with pytest.raises(LaymanError) as exc_info:
        util.parse_and_validate_external_table_uri_str(external_table_uri_str)
    exp_error = {'http_code': 400,
                 'code': 2,
                 'detail': {'parameter': 'db_connection',
                            'message': 'Unable to connect to database. Please check connection string, firewall settings, etc.',
                            'expected': util.EXTERNAL_TABLE_URI_PATTERN,
                            'found': {
                                'db_connection': external_table_uri_str}},
                 }
    exc_detail_msg = exc_info.value.to_dict()['detail']['detail']
    assert any(re.match(exp_err_msg_pattern, exc_detail_msg) for exp_err_msg_pattern in exp_err_msg_patterns), f'exc_detail_msg={exc_detail_msg}, exp_err_msg_patterns={exp_err_msg_patterns}'
    exp_error['detail']['detail'] = exc_info.value.to_dict()['detail']['detail']
    test_util.assert_error(exp_error, exc_info)


@pytest.mark.parametrize('external_table_uri_str, scheme', [
    ('', ''),
    (' ', ''),
    ('_', ''),
    ('$^&*(', ''),
    ('ščžýžý', ''),
    ('docker:docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', 'docker'),
    ('mysql://docker:docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', 'mysql'),
])
def test_validate_external_table_uri_str_parse(external_table_uri_str, scheme):
    with pytest.raises(LaymanError) as exc_info:
        util.parse_and_validate_external_table_uri_str(external_table_uri_str)
    exp_error = {'http_code': 400,
                 'code': 2,
                 'detail': {'parameter': 'db_connection',
                            'message': 'Parameter `db_connection` is expected to have URI scheme `postgresql`',
                            'expected': util.EXTERNAL_TABLE_URI_PATTERN,
                            'found': {
                                'db_connection': external_table_uri_str,
                                'uri_scheme': scheme,
                            },
                            },
                 }
    test_util.assert_error(exp_error, exc_info)
