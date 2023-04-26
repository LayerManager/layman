import json
import pytest

from layman import app, util as layman_util
from test_tools import process_client
from ... import static_data as data
from ..data import ensure_publication


def assert_operates_on(workspace, mapname, expected_layers, authz_headers):
    md_comparison = process_client.get_workspace_map_metadata_comparison(workspace, mapname, authz_headers)
    operates_on = md_comparison['metadata_properties']['operates_on']
    assert (operates_on['equal']), json.dumps(operates_on, indent=2)
    assert (operates_on['equal_or_null']), json.dumps(operates_on, indent=2)
    assert len(operates_on['values'].values()) == 2  # GET Map File, CSW

    for operates_on_value in operates_on['values'].values():
        for (layer_uuid, layer_title) in expected_layers:
            layer_record = next(rec for rec in operates_on_value
                                if rec['xlink:title'] == layer_title and layer_uuid in rec['xlink:href'])
            assert layer_record, f"Layer uuid={layer_uuid}, title={layer_title} not found in operates_on value {json.dumps(operates_on_value, indent=2)}"
        assert len(expected_layers) == len(
            operates_on_value), f"Expected layers {expected_layers}, found {json.dumps(operates_on_value, indent=2)}"


@pytest.mark.parametrize('workspace, publ_type, publication', data.LIST_INTERNAL_MAPS)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_map_with_unauthorized_layer(workspace, publ_type, publication):
    ensure_publication(workspace, publ_type, publication)

    operates_on_layers = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA]['operates_on']
    exp_operates_on = []
    for layer_workspace, layer_type, layer in operates_on_layers:
        with app.app_context():
            info = layman_util.get_publication_info(layer_workspace, layer_type, layer, context={'keys': ['uuid', 'title']})
            uuid = info['uuid']
            title = info['title']
        exp_operates_on.append((uuid, title))

    for headers in data.HEADERS.values():
        assert_operates_on(workspace, publication, exp_operates_on, authz_headers=headers)
