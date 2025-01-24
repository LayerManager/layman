import pytest

from geoserver import util as gs_util
from layman import app, settings, util as layman_util, names
from layman.common import geoserver as gs_common
from test_tools import process_client, role_service
from tests import EnumTestTypes, Publication
from tests.asserts.final.publication import util as assert_util
from tests.asserts.final.publication.geoserver_util import get_wms_layername
from tests.dynamic_data import base_test, base_test_classes

pytest_generate_tests = base_test.pytest_generate_tests


USERNAME = 'test_access_rights_role_user1'
USER_ROLE1_ROLE3_EVERYONE = {USERNAME, 'ROLE1', 'ROLE3', 'EVERYONE'}
USER_ROLE1 = {USERNAME, 'ROLE1'}
USER_ROLE1_ROLE2 = {USERNAME, 'ROLE1', 'ROLE2'}
ROLES = ['ROLE1', 'ROLE2', 'ROLE3']


@pytest.mark.usefixtures('oauth2_provider_mock')
class TestPublication(base_test.TestSingleRestPublication):
    workspace = 'test_access_rights_role'
    publication_type = None

    rest_parametrization = [
        base_test.PublicationByUsedServers,
        base_test_classes.RestMethod
    ]

    usernames_to_reserve = [
        USERNAME,
    ]

    external_tables_to_create = base_test_classes.EXTERNAL_TABLE_FOR_LAYERS_BY_USED_SERVERS

    def before_class(self):
        for role in ROLES:
            role_service.ensure_role(role)

    def after_class(self, request):
        if request.session.testsfailed == 0 and not request.config.option.nocleanup:
            for role in ROLES:
                role_service.delete_role(role)

    test_cases = [base_test.TestCaseType(key='role_test',
                                         publication=lambda publ_def, cls: Publication(cls.workspace,
                                                                                       publ_def.type,
                                                                                       None),
                                         rest_args={
                                             'access_rights': {
                                                 'read': ','.join(USER_ROLE1_ROLE2),
                                                 'write': ','.join(USER_ROLE1),
                                             },
                                             'actor_name': USERNAME,
                                         },
                                         post_before_test_args={
                                             'access_rights': {
                                                 'read': ','.join(USER_ROLE1_ROLE3_EVERYONE),
                                             }
                                         },
                                         type=EnumTestTypes.OPTIONAL,
                                         specific_types={frozenset([base_test.PublicationByUsedServers.LAYER_VECTOR_SLD, base_test_classes.RestMethod.POST]): EnumTestTypes.MANDATORY},
                                         )]

    def test_publication(self, publication, rest_method, rest_args):
        if rest_method.enum_item == base_test_classes.RestMethod.PATCH:
            info = process_client.get_workspace_publication(publication.type, publication.workspace, publication.name)
            assert set(info['access_rights']['read']) == USER_ROLE1_ROLE3_EVERYONE
            assert set(info['access_rights']['write']) == {'EVERYONE'}

        rest_method.fn(publication, args=rest_args)
        assert_util.is_publication_valid_and_complete(publication)

        info = process_client.get_workspace_publication(publication.type, publication.workspace, publication.name,
                                                        actor_name=USERNAME)
        for right, exp_rights in [('read', USER_ROLE1_ROLE2),
                                  ('write', USER_ROLE1),
                                  ]:
            assert set(info['access_rights'][right]) == exp_rights

            if publication.type == process_client.LAYER_TYPE:
                with app.app_context():
                    internal_info = layman_util.get_publication_info(publication.workspace, publication.type, publication.name, {'keys': ['geodata_type', 'wms', 'uuid']})

                geodata_type = internal_info['geodata_type']
                gs_workspace = internal_info['_wms']['workspace']

                gs_wfs_layername = names.get_layer_names_by_source(uuid=internal_info['uuid'], )['wfs']
                gs_wms_layername = get_wms_layername(publication.workspace, publication.name)
                workspaces_and_layers = [(publication.workspace, gs_wfs_layername), (gs_workspace, gs_wms_layername)] if geodata_type != settings.GEODATA_TYPE_RASTER else [gs_workspace]
                for wspace, gs_layername in workspaces_and_layers:
                    gs_expected_roles = gs_common.layman_users_and_roles_to_geoserver_roles(exp_rights)
                    rule = f'{wspace}.{gs_layername}.{right[0]}'
                    gs_roles = gs_util.get_security_roles(rule, settings.LAYMAN_GS_AUTH)
                    assert gs_expected_roles == gs_roles, f'gs_expected_roles={gs_expected_roles}, gs_roles={gs_roles}, wspace={wspace}, rule={rule}'
