from layman import app, util as layman_util
from test_tools import process_client


def same_title_in_source_and_rest_multi(workspace, publ_type, name, headers):
    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, name, context={'keys': ['title']})
    title = publ_info['title']
    infos = process_client.get_workspace_publications(publ_type, workspace, headers=headers)

    publication_infos = [info for info in infos if info['name'] == name]
    info = next(iter(publication_infos))
    assert info['title'] == title, f'publication_infos={publication_infos}'
