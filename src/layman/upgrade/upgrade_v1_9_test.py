import pytest

from . import upgrade_v1_9
from layman import settings, app
from layman.common import geoserver as gs_common
from test import process_client
DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

auth = settings.LAYMAN_GS_AUTH


def assert_roles(workspace,
                 layer,
                 expected_roles):
    for right_type in ['read', 'write']:
        rule = f'{workspace}.{layer}.{right_type[0]}'
        roles = gs_common.get_security_roles(rule, auth)
        assert roles == expected_roles


@pytest.mark.usefixtures('ensure_layman')
def test_geoserver_everyone_rights_repair():
    workspace = 'test_geoserver_everyone_rights_repair_workspace'
    layer = 'test_geoserver_everyone_rights_repair_layer'
    expected_roles1 = {'ROLE_ANONYMOUS'}
    expected_roles2 = {'ROLE_ANONYMOUS', 'ROLE_AUTHENTICATED'}

    process_client.publish_layer(workspace, layer)
    for right_type in ['read', 'write']:
        gs_common.ensure_layer_security_roles(workspace, layer, expected_roles1, right_type[0], auth)

    assert_roles(workspace, layer, expected_roles1)

    with app.app_context():
        upgrade_v1_9.geoserver_everyone_rights_repair()

    assert_roles(workspace, layer, expected_roles2)
