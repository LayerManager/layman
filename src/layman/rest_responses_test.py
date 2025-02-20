import datetime
import pytest
from dateutil.parser import parse

from db import util as db_util
from layman import app, settings, names
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
    layer_uuid = '97776002-efde-43f1-8618-26c0d69e4bf9'
    map_uuid = 'd2884b49-04a8-406a-940d-9dc2f5b2c8fa'
    common_params = {
        process_client.LAYER_TYPE: {
            'uuid': layer_uuid,
            'description': description,
        },
        process_client.MAP_TYPE: {
            'uuid': map_uuid,
            'description': description,
        }}

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
        'wfs_wms_status': settings.EnumWfsWmsStatus.AVAILABLE.value,
        'publication_type': 'layer',
        'used_in_maps': [],
    }
    expected_maps = {
        **expected_common_multi,
        'bounding_box': list(test_data.SMALL_MAP_BBOX),
        'native_crs': 'EPSG:3857',
        'native_bounding_box': list(test_data.SMALL_MAP_BBOX),
        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/maps/{publication}',
        'publication_type': 'map',
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
        'db': {'schema': workspace,
               'table': f"layer_{layer_uuid.replace('-', '_')}",
               'geo_column': 'wkb_geometry',
               },
        'geodata_type': 'vector',
        'file': {'paths': [f'layers/{layer_uuid}/input_file/{layer_uuid}.geojson'],
                 },
        'metadata': {'comparison_url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/layers/{publication}/'
                                       f'metadata-comparison',
                     'csw_url': f'{settings.CSW_PROXY_URL}',
                     'identifier': f"m-{layer_uuid}",
                     'record_url': None},
        'style': {'type': 'sld',
                  'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/layers/{publication}/style'},
        'thumbnail': {'path': f'layers/{layer_uuid}/thumbnail/{layer_uuid}.png',
                      'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/layers/{publication}/thumbnail'},
        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/layers/{publication}',
        'wfs': {'name': f'l_{layer_uuid}', 'url': f'{settings.LAYMAN_GS_PROXY_BASE_URL}{names.GEOSERVER_WFS_WORKSPACE}/wfs'},
        'wms': {'name': f'l_{layer_uuid}', 'url': f'{settings.LAYMAN_GS_PROXY_BASE_URL}{names.GEOSERVER_WMS_WORKSPACE}/ows'},
        'original_data_source': 'file',
        'used_in_maps': [],
    }
    expected_map = {
        **expected_common,
        'bounding_box': list(test_data.SMALL_MAP_BBOX),
        'native_crs': 'EPSG:3857',
        'native_bounding_box': list(test_data.SMALL_MAP_BBOX),
        'file': {'path': f'maps/{map_uuid}/input_file/{map_uuid}.json',
                 'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/maps/{publication}/file'},
        'metadata': {
            'comparison_url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/maps/{publication}/'
                              f'metadata-comparison',
            'csw_url': f'{settings.CSW_PROXY_URL}',
            'identifier': f"m-{map_uuid}",
            'record_url': None},
        'thumbnail': {'path': f'maps/{map_uuid}/thumbnail/{map_uuid}.png',
                      'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/maps/{publication}/thumbnail'},
        'url': f'http://{settings.LAYMAN_PROXY_SERVER_NAME}/rest/workspaces/{workspace}/maps/{publication}',
        'uuid': None,
    }

    @pytest.fixture(scope="class")
    def provide_data(self):
        for publication_type in process_client.PUBLICATION_TYPES:
            process_client.publish_workspace_publication(publication_type, self.workspace, self.publication, **self.common_params[publication_type], )
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
        pytest.param(process_client.get_publications, {'publication_type': None, 'query_params': {'order_by': 'title'}}, [expected_layers, expected_maps, ], id='get_publications'),
        pytest.param(process_client.get_layers, {}, [expected_layers], id='get_layers'),
        pytest.param(process_client.get_maps, {}, [expected_maps], id='get_maps'),
        pytest.param(process_client.get_layers, {'workspace': workspace}, [expected_layers], id='get_workspace_layers'),
        pytest.param(process_client.get_maps, {'workspace': workspace}, [expected_maps], id='get_workspace_maps'),
        pytest.param(process_client.get_workspace_layer, {'workspace': workspace, 'name': publication}, expected_layer, id='get_workspace_layer'),
        pytest.param(process_client.get_workspace_map, {'workspace': workspace, 'name': publication}, expected_map, id='get_workspace_map'),
    ])
    def test_rest_responses(query_method, method_params, expected_info, ):
        response = query_method(**method_params)
        if isinstance(response, list):
            assert len(response) == len(expected_info)
            for idx, info in enumerate(response):
                TestResponsesClass.compare_infos(info, expected_info[idx], '/')
        else:
            info = response
            TestResponsesClass.compare_infos(info, expected_info, '/')
