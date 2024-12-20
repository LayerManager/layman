import pytest

from db import util as db_util
from layman import app, settings
from layman.common.prime_db_schema import publications
from test_tools import process_client
from . import upgrade_v2_0


DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman')
@pytest.mark.parametrize('name, publ_type, definition', [
    ('test_vector_layer_sld', process_client.LAYER_TYPE, {}),
    ('test_vector_qml_layer', process_client.LAYER_TYPE, {'style_file': 'sample/style/small_layer.qml'}),
    ('test_raster_layer', process_client.LAYER_TYPE, {'file_paths': [
        'sample/layman.layer/sample_tif_tfw_rgba_opaque.tfw',
        'sample/layman.layer/sample_tif_tfw_rgba_opaque.tif',
    ]}),
    ('test_map', process_client.MAP_TYPE, {}),
])
def test_table_name_migration(name, publ_type, definition):
    workspace = 'test_description_migration'

    description = f'Description of {name}'
    process_client.publish_workspace_publication(publ_type, workspace, name,
                                                 description=description,
                                                 **definition)

    assert process_client.get_workspace_publication(publ_type, workspace, name)['description'] == description
    infos = publications.get_publication_infos(workspace)
    assert infos[(workspace, publ_type, name)]['description'] == description

    statement = f'''
    update {DB_SCHEMA}.publications set
      description = null
    ;'''
    with app.app_context():
        db_util.run_statement(statement)

    infos = publications.get_publication_infos(workspace)
    assert infos[(workspace, publ_type, name)]['description'] is None

    with app.app_context():
        upgrade_v2_0.adjust_publications_description()

    assert process_client.get_workspace_publication(publ_type, workspace, name)['description'] == description
    infos = publications.get_publication_infos(workspace)
    assert infos[(workspace, publ_type, name)]['description'] == description

    process_client.delete_workspace_publication(publ_type, workspace, name)
