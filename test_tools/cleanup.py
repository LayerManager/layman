from test_tools import external_db
from test_tools import process_client
from tests.asserts import util


def cleanup_publications(request, publications, *, force=False):
    if request.session.testsfailed == 0 and (not request.config.option.nocleanup or force):
        for publication in publications:
            if util.get_publication_exists(publication):
                headers = util.get_publication_header(publication)
                process_client.delete_workspace_publication(publication.type, publication.workspace, publication.name,
                                                            headers=headers)


def cleanup_external_tables(request, tables, *, force=False):
    if request.session.testsfailed == 0 and (not request.config.option.nocleanup or force):
        for schema, table in tables:
            external_db.drop_table(schema, table, if_exists=True)
