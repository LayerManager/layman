import json
import requests
from jsonschema import validate, Draft7Validator
from werkzeug.datastructures import FileStorage
import pytest

from layman import app, settings, util as layman_util
from layman.map.prime_db_schema import table as prime_db_schema_table
from layman.map.filesystem import input_file
from layman.map import util as map_util, MAP_TYPE
from layman.common.filesystem import uuid as uuid_common
from layman.uuid import generate_uuid
from test_tools import assert_util, process_client
from . import upgrade_v1_16
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

EXP_BBOXES = {
    '3857': [1627490.9553976597, 6547334.172794042, 1716546.5480322787, 6589515.35758913],
    '4326': [14.62, 50.58, 15.42, 50.82],
}


def provide_map(workspace, map, *, file_path):
    access_rights = {'read': [settings.RIGHTS_EVERYONE_ROLE], 'write': [settings.RIGHTS_EVERYONE_ROLE], }
    with app.app_context():
        uuid_str = generate_uuid()
        with open(file_path, 'rb') as file:
            file = FileStorage(file)
            input_file.save_map_files(
                workspace, map, [file])
        prime_db_schema_table.post_map(workspace,
                                       map,
                                       uuid_str,
                                       map,
                                       None,
                                       access_rights,
                                       None,
                                       )
        uuid_common.assign_publication_uuid(MAP_TYPE, workspace, map, uuid_str=uuid_str)


@pytest.mark.usefixtures('ensure_layman')
@pytest.mark.parametrize('epsg_code', [
    '3857',
    '4326',
])
def test_adjust_maps(epsg_code):
    workspace = 'test_v1_16_maps'
    map = f'epsg_{epsg_code}'

    url = 'https://raw.githubusercontent.com/hslayers/map-compositions/2.0.0/schema.json'

    file_path = f'src/layman/upgrade/map_1_1_0_{epsg_code}.json'
    provide_map(workspace, map, file_path=file_path)
    with app.app_context():
        upgrade_v1_16.adjust_maps()

        info = layman_util.get_publication_info(workspace, MAP_TYPE, map,
                                                context={'keys': ['native_bounding_box', 'bounding_box', 'native_crs']})
        assert info['native_crs'] == f'EPSG:{epsg_code}', info
        assert_util.assert_same_bboxes(EXP_BBOXES[epsg_code], info['native_bounding_box'], 0.00001)
        assert_util.assert_same_bboxes(EXP_BBOXES['3857'], info['bounding_box'], 0.00001)

        res = requests.get(url,
                           timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
        res.raise_for_status()
        schema_txt = res.text
        schema_json = json.loads(schema_txt)

        mapjson = map_util.get_map_file_json(workspace, map)
        validator = Draft7Validator(schema_json)
        assert validator.is_valid(mapjson), [
            {
                'message': e.message,
                'absolute_path': list(e.absolute_path),
            }
            for e in validator.iter_errors(mapjson)
        ]
        validate(instance=mapjson, schema=schema_json)

    process_client.delete_workspace_map(workspace, map)


@pytest.mark.usefixtures('ensure_layman')
@pytest.mark.parametrize('epsg_code', [
    '3030',
])
def test_adjust_maps_fail(epsg_code):
    workspace = 'test_v1_16_maps'
    map = f'epsg_{epsg_code}'
    file_path = f'src/layman/upgrade/map_1_1_0_{epsg_code}.json'
    provide_map(workspace, map, file_path=file_path)

    with app.app_context():
        with pytest.raises(AssertionError):
            upgrade_v1_16.adjust_maps()
