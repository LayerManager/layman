import datetime

import test.data
from test import process_client, data as test_data

import pytest
from dateutil.parser import parse

from layman import app, settings
from layman.common.prime_db_schema import util as db_util
from layman.rest_publication_test import db_schema


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
    common_params = dict()

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
        'bounding_box': test_data.SMALL_LAYER_BBOX,
        'url': f'http://{settings.LAYMAN_SERVER_NAME}/rest/workspaces/{workspace}/'
               f'layers/{publication}',
    }
    expected_maps = {
        **expected_common_multi,
        'bounding_box': test_data.SMALL_MAP_BBOX,
        'url': f'http://{settings.LAYMAN_SERVER_NAME}/rest/workspaces/{workspace}/'
               f'maps/{publication}',
    }

    @pytest.fixture(scope="class")
    def provide_data(self):
        for publication_type in process_client.PUBLICATION_TYPES:
            process_client.publish_workspace_publication(publication_type, self.workspace, self.publication, **self.common_params,)
        yield
        for publication_type in process_client.PUBLICATION_TYPES:
            process_client.delete_workspace_publication(publication_type, self.workspace, self.publication, )

    @staticmethod
    @pytest.mark.usefixtures('ensure_layman', 'provide_data')
    @pytest.mark.parametrize('query_method, method_params, expected_info', [
        (process_client.get_layers, dict(), expected_layers),
        (process_client.get_maps, dict(), expected_maps),
        (process_client.get_workspace_layers, {'workspace': workspace}, expected_layers),
        (process_client.get_workspace_maps, {'workspace': workspace}, expected_maps),
    ])
    def test_rest_responses(query_method, method_params, expected_info, ):
        response = query_method(**method_params)
        assert len(response) == 1
        info = response[0]
        assert len(info) == len(expected_info), info
        for key, value in expected_info.items():
            assert key in info.keys()
            if value:
                assert info[key] == value
