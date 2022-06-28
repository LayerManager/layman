import pytest

from db import util as db_util
from layman import app, settings
from test_tools import process_client, assert_util
from . import upgrade_v1_14

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA


@pytest.mark.usefixtures('ensure_layman')
@pytest.mark.skip(reason="Waiting for decision about upgrading to v1.17 only from v1.14+")
def test_bbox_crop():
    def assert_out_of_the_box_publications(expected_count):
        query = f'''select count(*)
        from {DB_SCHEMA}.publications p
        where st_xMin(p.bbox) < -20026376.39
           or st_yMin(p.bbox) < -20048966.10
           or st_xMax(p.bbox) > 20026376.39
           or st_yMax(p.bbox) > 20048966.10
        ;'''
        with app.app_context():
            cnt = db_util.run_query(query)
        assert cnt[0][0] == expected_count, cnt

    main_workspace = 'test_bbox_crop_workspace'

    publications = [
        (process_client.LAYER_TYPE, main_workspace, 'test_bbox_crop_layer', {'file_paths': [
            'sample/layman.layer/small_layer.cpg',
            'sample/layman.layer/small_layer.dbf',
            'sample/layman.layer/small_layer.prj',
            'sample/layman.layer/small_layer.shp',
            'sample/layman.layer/small_layer.shx',
        ], },),
        (process_client.LAYER_TYPE, main_workspace, 'test_bbox_crop_qml_layer', {'file_paths': [
            'sample/layman.layer/small_layer.cpg',
            'sample/layman.layer/small_layer.dbf',
            'sample/layman.layer/small_layer.prj',
            'sample/layman.layer/small_layer.shp',
            'sample/layman.layer/small_layer.shx',
        ], 'style_file': 'sample/style/small_layer.qml'},),
        (process_client.MAP_TYPE, main_workspace, 'test_bbox_crop_map', dict(),),
    ]
    for publication_type, workspace, publication, params in publications:
        process_client.publish_workspace_publication(publication_type, workspace, publication, **params)

    big_bbox = (-20026376.39 - 1,
                -20048966.10 - 1,
                20026376.39 + 1,
                20048966.10 + 1,
                )

    query = f'''update {DB_SCHEMA}.publications set
    bbox = ST_MakeBox2D(ST_Point(%s, %s), ST_Point(%s ,%s))
    where type = %s
      and name = %s
      and id_workspace = (select w.id from {DB_SCHEMA}.workspaces w where w.name = %s);'''

    for publication_type, workspace, publication, _ in publications:
        params = big_bbox + (publication_type, publication, workspace,)
        with app.app_context():
            db_util.run_statement(query, params)

    assert_out_of_the_box_publications(len(publications))

    with app.app_context():
        upgrade_v1_14.crop_bbox()

    assert_out_of_the_box_publications(0)

    for publication_type, workspace, publication, _ in publications:
        if publication_type == process_client.LAYER_TYPE:
            assert_util.assert_all_sources_bbox(workspace, publication, (-20026376.39, -20048966.10, 20026376.39, 20048966.10, ))

    for publication_type, workspace, publication, _ in publications:
        process_client.delete_workspace_publication(publication_type, workspace, publication)
