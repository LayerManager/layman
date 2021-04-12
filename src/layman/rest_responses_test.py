import datetime

import pytest
from dateutil.parser import parse

import process_client
from layman import app
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
