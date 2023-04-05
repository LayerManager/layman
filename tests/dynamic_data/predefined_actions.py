from tests.asserts import processing
from test_tools import process_client
from .. import dynamic_data as consts, Action


_POST_ZIP_SHP_WITHOUT_PRJ_DEFINITION = {
    'file_paths': [
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.cpg',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.dbf',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shp',
        'tmp/naturalearth/110m/cultural/ne_110m_admin_0_boundary_lines_land.shx',
    ],
}

POST_ZIP_SHP_WITHOUT_PRJ_WITH_CRS = {
    consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
        **_POST_ZIP_SHP_WITHOUT_PRJ_DEFINITION,
        'compress': True,
        'crs': 'EPSG:4326',
    }),
    consts.KEY_RESPONSE_ASSERTS: [
        Action(processing.response.valid_post, {}),
    ],
}
