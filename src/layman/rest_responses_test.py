import datetime
import pytest
from dateutil.parser import parse

from db import util as db_util
from layman import app, settings
from layman.rest_publication_test import db_schema
from test_tools import process_client, data as test_data


@pytest.mark.parametrize('publication_type', process_client.PUBLICATION_TYPES)
@pytest.mark.usefixtures('ensure_layman')
def test_updated_at(publication_type):
    workspace = 'test_update_at_workspace'
    publication = 'test_update_at_publication'

    query = f'''
    select p.updated_at
    from {db_schema}.publications p inner join
         {db_schema}.workspaces w on p.id_workspace = w.id
    where w.name = %s
      and p.type = %s
      and p.name = %s
    ;'''

    timestamp1 = datetime.datetime.now(datetime.timezone.utc)
    process_client.publish_workspace_publication(publication_type, workspace, publication)
    timestamp2 = datetime.datetime.now(datetime.timezone.utc)

    with app.app_context():
        results = db_util.run_query(query, (workspace, publication_type, publication))
    assert len(results) == 1 and len(results[0]) == 1, results
    updated_at_db = results[0][0]
    assert timestamp1 < updated_at_db < timestamp2

    info = process_client.get_workspace_publication(publication_type, workspace, publication)
    updated_at_rest_str = info['updated_at']
    updated_at_rest = parse(updated_at_rest_str)
    assert timestamp1 < updated_at_rest < timestamp2

    timestamp3 = datetime.datetime.now(datetime.timezone.utc)
    process_client.patch_workspace_publication(publication_type, workspace, publication, title='Title')
    timestamp4 = datetime.datetime.now(datetime.timezone.utc)

    with app.app_context():
        results = db_util.run_query(query, (workspace, publication_type, publication))
    assert len(results) == 1 and len(results[0]) == 1, results
    updated_at_db = results[0][0]
    assert timestamp3 < updated_at_db < timestamp4

    info = process_client.get_workspace_publication(publication_type, workspace, publication)
    updated_at_rest_str = info['updated_at']
    updated_at_rest = parse(updated_at_rest_str)
    assert timestamp3 < updated_at_rest < timestamp4

    process_client.delete_workspace_publication(publication_type, workspace, publication)


class TestResponsesClass:
    workspace = 'test_responses_workspace'
    publication = 'test_responses_publication'
    description = 'Toto je popisek.'
    common_params = {
        'description': description,
    }

    expected_common_multi = {
        'access_rights': {'read': ['EVERYONE'], 'write': ['EVERYONE']},
        'name': publication,
        'title': publication,
        'updated_at': None,
        'uuid': None,
        'workspace': workspace,
    }
    expected_layers = {
        **expected_common_multi,
        'bounding_box': list(test_data.SMALL_LAYER_BBOX),
        'native_crs': 'EPSG:4326',
        'native_bounding_box': list(test_data.SMALL_LAYER_NATIVE_BBOX),
        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/layers/{publication}',
        'geodata_type': settings.GEODATA_TYPE_VECTOR,
        'file': {
            'file_type': settings.GEODATA_TYPE_VECTOR,
        },
    }
    expected_maps = {
        **expected_common_multi,
        'bounding_box': list(test_data.SMALL_MAP_BBOX),
        'native_crs': 'EPSG:3857',
        'native_bounding_box': list(test_data.SMALL_MAP_BBOX),
        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/maps/{publication}',
    }

    expected_common = {
        'access_rights': {'read': ['EVERYONE'], 'write': ['EVERYONE']},
        'layman_metadata': {'publication_status': 'COMPLETE'},
        'description': description,
        'name': publication,
        'title': publication,
        'updated_at': None,
        'uuid': None,
    }
    expected_layer = {
        **expected_common,
        'bounding_box': list(test_data.SMALL_LAYER_BBOX),
        'native_crs': 'EPSG:4326',
        'native_bounding_box': list(test_data.SMALL_LAYER_NATIVE_BBOX),
        'db_table': {'name': None},
        'db': {'schema': workspace,
               'table': None,
               'geo_column': 'wkb_geometry',
               },
        'geodata_type': 'vector',
        'file': {'path': f'layers/{publication}/input_file/{publication}.geojson',
                 'paths': [f'layers/{publication}/input_file/{publication}.geojson'],
                 'file_type': 'vector',
                 },
        'metadata': {'comparison_url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/layers/{publication}/'
                                       f'metadata-comparison',
                     'csw_url': f'{settings.CSW_PROXY_URL}',
                     'identifier': None,
                     'record_url': None},
        'sld': {'type': 'sld',
                'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/layers/{publication}/style'},
        'style': {'type': 'sld',
                  'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/layers/{publication}/style'},
        'thumbnail': {'path': f'layers/{publication}/thumbnail/{publication}.png',
                      'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/layers/{publication}/thumbnail'},
        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/layers/{publication}',
        'wfs': {'url': f'{settings.LAYMAN_GS_PROXY_BASE_URL}{workspace}/wfs'},
        'wms': {'url': f'{settings.LAYMAN_GS_PROXY_BASE_URL}{workspace}_wms/ows'},
        'original_data_source': 'file',
    }
    expected_map = {
        **expected_common,
        'bounding_box': list(test_data.SMALL_MAP_BBOX),
        'native_crs': 'EPSG:3857',
        'native_bounding_box': list(test_data.SMALL_MAP_BBOX),
        'file': {'path': f'maps/{publication}/input_file/{publication}.json',
                 'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/maps/{publication}/file'},
        'metadata': {
            'comparison_url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/maps/{publication}/'
                              f'metadata-comparison',
            'csw_url': f'{settings.CSW_PROXY_URL}',
            'identifier': None,
            'record_url': None},
        'thumbnail': {'path': f'maps/{publication}/thumbnail/{publication}.png',
                      'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/maps/{publication}/thumbnail'},
        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/maps/{publication}',
        'uuid': None,
    }

    @pytest.fixture(scope="class")
    def provide_data(self):
        for publication_type in process_client.PUBLICATION_TYPES:
            process_client.publish_workspace_publication(publication_type, self.workspace, self.publication, **self.common_params,)
        yield
        for publication_type in process_client.PUBLICATION_TYPES:
            process_client.delete_workspace_publication(publication_type, self.workspace, self.publication, )

    @staticmethod
    def compare_infos(info, expected_info, path):
        assert info.keys() == expected_info.keys(), (info, path)
        for key, value in expected_info.items():
            if isinstance(value, dict):
                TestResponsesClass.compare_infos(info[key], value, '/' + key + '/')
            elif value:
                assert info[key] == value, path + key

    @staticmethod
    @pytest.mark.usefixtures('ensure_layman', 'provide_data')
    @pytest.mark.parametrize('query_method, method_params, expected_info', [
        pytest.param(process_client.get_layers, {}, expected_layers, id='get_layers'),
        pytest.param(process_client.get_maps, {}, expected_maps, id='get_maps'),
        pytest.param(process_client.get_workspace_layers, {'workspace': workspace}, expected_layers, id='get_workspace_layers'),
        pytest.param(process_client.get_workspace_maps, {'workspace': workspace}, expected_maps, id='get_workspace_maps'),
        pytest.param(process_client.get_workspace_layer, {'workspace': workspace, 'name': publication}, expected_layer, id='get_workspace_layer'),
        pytest.param(process_client.get_workspace_map, {'workspace': workspace, 'name': publication}, expected_map, id='get_workspace_map'),
    ])
    def test_rest_responses(query_method, method_params, expected_info, ):
        response = query_method(**method_params)
        if isinstance(response, list):
            assert len(response) == 1
            info = response[0]
        else:
            info = response
        TestResponsesClass.compare_infos(info, expected_info, '/')
