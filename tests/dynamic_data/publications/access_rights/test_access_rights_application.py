import copy
import os
import inspect
import pytest

from geoserver.error import Error as GS_Error
from layman import app, settings, LaymanError
from layman.layer import db
from layman.util import get_publication_uuid
from layman.layer.layer_class import Layer
from test_tools import process_client, role_service as role_service_util
from test_tools.data import wfs
from tests import Publication4Test, EnumTestTypes, EnumTestKeys
from tests.asserts.final.publication import geoserver_proxy, util as assert_publ_util
from tests.dynamic_data import base_test

OWNER = 'test_access_rights_application_owner'
READER_BY_USERNAME = 'test_access_rights_application_reader_by_username'
READER_BY_ROLE = 'test_access_rights_application_reader_by_role'

LAYER_NO_ACCESS = Publication4Test(OWNER, process_client.LAYER_TYPE, 'test_no_access_layer')
LAYER_ACCESS_RIGHTS = Publication4Test(OWNER, process_client.LAYER_TYPE, 'test_access_rights_layer')

ENDPOINTS_TO_TEST = {
    process_client.LAYER_TYPE: [
        (process_client.get_workspace_publication, {}),
        (process_client.get_workspace_publication_metadata_comparison, {}),
        (process_client.get_workspace_layer_style, {}),
        (process_client.get_uuid_publication_thumbnail, {}),
        # process_client.get_workspace_layer_chunk,
        (process_client.patch_workspace_publication, {'title': 'New title'}),
        (process_client.patch_workspace_publication, {'file_paths': ['sample/layman.layer/small_layer.geojson']}),
    ],
    process_client.MAP_TYPE: [
        (process_client.get_workspace_publication, {}),
        (process_client.get_workspace_map_file, {}),
        (process_client.get_workspace_publication_metadata_comparison, {}),
        (process_client.get_uuid_publication_thumbnail, {}),
        (process_client.patch_workspace_publication, {'title': 'New title'}),
        (process_client.patch_workspace_publication, {'file_paths': ['sample/layman.map/small_map.json']}),
    ],
}

ENDPOINTS_TO_TEST_NEGATIVE_ONLY = [
    (process_client.delete_workspace_publication, {}),
]

GEOSERVER_METHODS_TO_TEST = [
    (geoserver_proxy.is_complete_in_workspace_wms_1_3_0, {}),
    (geoserver_proxy.workspace_wfs_2_0_0_capabilities_available_if_vector, {}),
]

WFST_METHODS_TO_TEST = {
    'insert_lines': {'xml_getter': wfs.get_wfs20_insert_lines},
    'insert_points_new_attr': {'xml_getter': wfs.get_wfs20_insert_points_new_attr, 'attr_names': ['inexist_attr1', 'inexist_attr2']},
    'update_points_new_attr': {'xml_getter': wfs.get_wfs20_update_points_new_attr, 'attr_names': ['inexist_attr3', 'inexist_attr4']},
}


def pytest_generate_tests(metafunc):
    # https://docs.pytest.org/en/6.2.x/parametrize.html#pytest-generate-tests
    test_type_str = os.getenv(EnumTestKeys.TYPE.value) or EnumTestTypes.MANDATORY.value
    test_type = EnumTestTypes(test_type_str)
    cls = metafunc.cls
    test_fn = metafunc.function
    arg_names = [a for a in inspect.getfullargspec(test_fn).args if a != 'self']
    argvalues = []
    ids = []

    test_cases = cls.test_cases[test_fn.__name__]
    test_cases_for_type = [test_case for test_case in test_cases if
                           test_type == EnumTestTypes.OPTIONAL or test_case.type == EnumTestTypes.MANDATORY]
    for test_case in test_cases_for_type:
        assert not test_case.key, f"Not yet implemented"
        assert not test_case.specific_params, f"Not yet implemented"
        assert not test_case.specific_types, f"Not yet implemented"
        assert not test_case.parametrization, f"Not yet implemented"
        assert not test_case.post_before_test_args, f"Not yet implemented"
        assert test_case.type in {EnumTestTypes.MANDATORY, EnumTestTypes.OPTIONAL}
        arg_name_to_value = {
            'publication': test_case.publication,
            'publication_type': test_case.publication_type,
            'rest_method': test_case.rest_method,
            'rest_args': copy.deepcopy(test_case.rest_args),
            'params': copy.deepcopy(test_case.params),
        }
        arg_values = [arg_name_to_value[n] for n in arg_names]

        argvalues.append(pytest.param(*arg_values, marks=test_case.marks))
        ids.append(test_case.pytest_id)
    metafunc.parametrize(
        argnames=', '.join(arg_names),
        argvalues=argvalues,
        ids=ids,
    )


def add_publication_test_cases_to_list(tc_list, publication, user, endpoints_to_test):
    all_args = {
        'workspace': publication.workspace,
        'name': publication.name,
        'uuid': publication.uuid,
        'layer': publication.name,
        'actor_name': user,
        'publication_type': publication.type,
        'publ_type': publication.type,
    }
    for method, raw_args in endpoints_to_test:
        # pylint: disable=comparison-with-callable
        test_type = EnumTestTypes.MANDATORY if user in {
            READER_BY_USERNAME,
            READER_BY_ROLE} and method in {process_client.get_workspace_publication,
                                           geoserver_proxy.is_complete_in_workspace_wms_1_3_0} and publication in {LAYER_ACCESS_RIGHTS,
                                                                                                                   LAYER_NO_ACCESS} else EnumTestTypes.OPTIONAL

        pytest_id = f'{method.__name__}__{user.split("_")[-1]}__{publication.name[5:]}{("__" + next(iter(raw_args.keys()))) if raw_args else ""}'
        method_args = inspect.getfullargspec(method).args + inspect.getfullargspec(method).kwonlyargs

        args = copy.deepcopy(raw_args)
        if method is process_client.get_uuid_publication_thumbnail and 'uuid' not in args:
            args.update({
                'workspace': publication.workspace,
                'name': publication.name,
            })
        args.update({
            key: value for key, value in all_args.items()
            if key in method_args and key not in args
        })
        test_case = base_test.TestCaseType(
            pytest_id=pytest_id,
            rest_method=method,
            rest_args=args,
            type=test_type,
        )
        tc_list.append(test_case)


def generate_positive_test_cases(publications_user_can_read):
    tc_list = []
    for user, publications in publications_user_can_read.items():
        for publication in publications:
            add_publication_test_cases_to_list(tc_list, publication, user, ENDPOINTS_TO_TEST[publication.type])
    return tc_list


def generate_negative_test_cases(publications_user_can_read, publication_all):
    tc_list = []
    for user, available_publications in publications_user_can_read.items():
        for publication in publication_all:
            if publication in available_publications:
                continue
            endpoints_to_test = {publ_type: endpoints + ENDPOINTS_TO_TEST_NEGATIVE_ONLY for publ_type, endpoints in ENDPOINTS_TO_TEST.items()}
            add_publication_test_cases_to_list(tc_list, publication, user, endpoints_to_test[publication.type])
    return tc_list


def generate_multiendpoint_test_cases(publications_user_can_read, workspace, ):
    tc_list = []
    for user, publications in publications_user_can_read.items():
        for method, type_filter, workspace_filter in [
            (process_client.get_publications, None, None),
            (process_client.get_publications, process_client.LAYER_TYPE, None),
            (process_client.get_publications, process_client.MAP_TYPE, None),
            (process_client.get_publications, process_client.LAYER_TYPE, workspace),
            (process_client.get_publications, process_client.MAP_TYPE, workspace),
        ]:
            test_type = EnumTestTypes.MANDATORY if method == process_client.get_publications and type_filter is None and workspace_filter is None and user in {READER_BY_USERNAME, READER_BY_ROLE} else EnumTestTypes.OPTIONAL
            pytest_id = f'GET__{type_filter.split(".")[1] if type_filter else "publication"}s__{workspace_filter}__{user.split("_")[-1]}'
            available_publications = [(publication.workspace, publication.type, publication.name) for publication in publications
                                      if (not type_filter or publication.type == type_filter)
                                      and (not workspace_filter or publication.workspace == workspace_filter)
                                      ]
            available_publications.sort(key=lambda x: (x[0], x[2], x[1]))
            test_case = base_test.TestCaseType(pytest_id=pytest_id,
                                               rest_method=method,
                                               rest_args={
                                                   'publication_type': type_filter,
                                                   'workspace': workspace_filter,
                                                   'actor_name': user,
                                               },
                                               params={'exp_publications': available_publications},
                                               type=test_type,
                                               )

            tc_list.append(test_case)
    return tc_list


def generate_positive_geoserver_test_cases(publications_user_can_read):
    tc_list = []
    for user, publications in publications_user_can_read.items():
        for publication in publications:
            if publication.type == process_client.LAYER_TYPE:
                add_publication_test_cases_to_list(tc_list, publication, user, GEOSERVER_METHODS_TO_TEST)
    return tc_list


def generate_geoserver_negative_test_cases(publications_user_can_read, publication_all):
    tc_list = []
    for user, available_publications in publications_user_can_read.items():
        for publication in publication_all:
            if publication not in available_publications and publication.type == process_client.LAYER_TYPE:
                add_publication_test_cases_to_list(tc_list, publication, user, GEOSERVER_METHODS_TO_TEST)
    return tc_list


def add_wfst_publication_test_cases_to_list(tc_list, publication, user, username_for_id, test_cases):
    method = process_client.post_wfst_with_xml_getter
    all_args = {
        'workspace': publication.workspace,
        'name': publication.name,
        'layer': publication.name,
        'actor_name': user,
        'publication_type': publication.type,
        'publ_type': publication.type,
    }
    for key, test_case in test_cases.items():
        test_type = EnumTestTypes.MANDATORY if user in {
            READER_BY_USERNAME, READER_BY_ROLE} and key == 'insert_lines' and publication in (LAYER_ACCESS_RIGHTS, LAYER_NO_ACCESS) else EnumTestTypes.OPTIONAL

        attribs = [attr + f'_{username_for_id.lower()}' for attr in test_case.get('attr_names', [])]
        args = {
            'xml_getter': test_case['xml_getter'],
            'xml_getter_params': {'attr_names': attribs} if attribs else {},
        }
        params = {
            'headers': process_client.get_authz_headers(user) if user != settings.ANONYM_USER else {}
        }
        if attribs:
            params['new_attribs'] = attribs
        pytest_id = f'{method.__name__}__{user.split("_")[-1]}__{publication.name[5:]}__{key}'
        method_args = inspect.getfullargspec(method).args + inspect.getfullargspec(method).kwonlyargs

        test_case = base_test.TestCaseType(pytest_id=pytest_id,
                                           publication=publication,
                                           publication_type=process_client.LAYER_TYPE,
                                           rest_method=method,
                                           rest_args={**args, **{
                                               key: value for key, value in all_args.items() if key in method_args
                                           }},
                                           params=params,
                                           type=test_type,
                                           )

        tc_list.append(test_case)


def generate_wfst_negative_test_cases(publications_user_can_read, publication_all, test_cases):
    tc_list = []
    for user, available_publications in publications_user_can_read.items():
        username_for_id = user.replace('--', "")
        for publication in [publication for publication in publication_all if
                            publication not in available_publications and publication.type == process_client.LAYER_TYPE]:
            add_wfst_publication_test_cases_to_list(tc_list, publication, user, username_for_id, test_cases)
    return tc_list


def generate_positive_wfst_test_cases(publications_user_can_read, test_cases):
    tc_list = []
    for user, publications in publications_user_can_read.items():
        username_for_id = user.replace('--', "")
        for publication in [publication for publication in publications if publication.type == process_client.LAYER_TYPE]:
            add_wfst_publication_test_cases_to_list(tc_list, publication, user, username_for_id, test_cases)
    return tc_list


@pytest.mark.timeout(60)
@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
class TestAccessRights:
    OWNER = OWNER
    READER_BY_USERNAME = READER_BY_USERNAME
    READER_BY_ROLE = READER_BY_ROLE
    OTHER_USER = 'test_access_rights_application_other_user'
    ROLE = 'TEST_ACCESS_RIGHTS_APPLICATION_ROLE'
    OTHER_ROLE = 'TEST_ACCESS_RIGHTS_APPLICATION_OTHER_ROLE'
    NON_EXISTING_ROLE = 'TEST_ACCESS_RIGHTS_NON_EXISTING_ROLE'

    LAYER_NO_ACCESS = LAYER_NO_ACCESS
    LAYER_ACCESS_RIGHTS = LAYER_ACCESS_RIGHTS
    LAYER_EVERYONE_ACCESS = Publication4Test(OWNER, process_client.LAYER_TYPE, 'test_everyone_access_layer')
    MAP_NO_ACCESS = Publication4Test(OWNER, process_client.MAP_TYPE, 'test_no_access_map')
    MAP_ACCESS_RIGHTS = Publication4Test(OWNER, process_client.MAP_TYPE, 'test_access_rights_map')
    MAP_EVERYONE_ACCESS = Publication4Test(OWNER, process_client.MAP_TYPE, 'test_everyone_access_map')

    ACCESS_RIGHT_NO_ACCESS = {
        'read': OWNER,
        'write': OWNER,
    }
    ACCESS_RIGHTS_ACCESS = {
        'read': f'{OWNER}, {READER_BY_USERNAME}, {ROLE}, {NON_EXISTING_ROLE}',
        'write': f'{OWNER}, {READER_BY_USERNAME}, {ROLE}, {NON_EXISTING_ROLE}',
    }
    ACCESS_RIGHTS_EVERYONE_ACCESS = {
        'read': settings.RIGHTS_EVERYONE_ROLE,
        'write': settings.RIGHTS_EVERYONE_ROLE,
    }

    PUBLICATIONS_DEFS = [
        # Publication, posted access rights, deleter
        (LAYER_NO_ACCESS, ACCESS_RIGHT_NO_ACCESS, OWNER),
        (LAYER_ACCESS_RIGHTS, ACCESS_RIGHTS_ACCESS, READER_BY_USERNAME),
        (LAYER_EVERYONE_ACCESS, ACCESS_RIGHTS_EVERYONE_ACCESS, OTHER_USER),
        (MAP_NO_ACCESS, ACCESS_RIGHT_NO_ACCESS, OWNER),
        (MAP_ACCESS_RIGHTS, ACCESS_RIGHTS_ACCESS, READER_BY_USERNAME),
        (MAP_EVERYONE_ACCESS, ACCESS_RIGHTS_EVERYONE_ACCESS, OTHER_USER),
    ]

    PUBLICATIONS = [publication for publication, _, _ in PUBLICATIONS_DEFS]

    PUBLICATIONS_BY_USER = {
        OWNER: [publication for publication, _, _ in PUBLICATIONS_DEFS],
        READER_BY_USERNAME: [LAYER_ACCESS_RIGHTS, LAYER_EVERYONE_ACCESS, MAP_ACCESS_RIGHTS, MAP_EVERYONE_ACCESS, ],
        READER_BY_ROLE: [LAYER_ACCESS_RIGHTS, LAYER_EVERYONE_ACCESS, MAP_ACCESS_RIGHTS, MAP_EVERYONE_ACCESS, ],
        OTHER_USER: [LAYER_EVERYONE_ACCESS, MAP_EVERYONE_ACCESS, ],
        settings.ANONYM_USER: [LAYER_EVERYONE_ACCESS, MAP_EVERYONE_ACCESS, ],
    }

    test_cases = {
        'test_single_positive': generate_positive_test_cases(PUBLICATIONS_BY_USER) + generate_positive_geoserver_test_cases(PUBLICATIONS_BY_USER),
        'test_single_negative': generate_negative_test_cases(PUBLICATIONS_BY_USER, PUBLICATIONS),
        'test_multiendpoint': generate_multiendpoint_test_cases(PUBLICATIONS_BY_USER, OWNER),
        'test_geoserver_negative': generate_geoserver_negative_test_cases(PUBLICATIONS_BY_USER, PUBLICATIONS),
        'test_wfst_positive': generate_positive_wfst_test_cases(PUBLICATIONS_BY_USER, WFST_METHODS_TO_TEST),
        'test_wfst_negative': generate_wfst_negative_test_cases(PUBLICATIONS_BY_USER, PUBLICATIONS, WFST_METHODS_TO_TEST),
    }

    @pytest.fixture(scope='class', autouse=True)
    def class_fixture(self, request):
        process_client.ensure_reserved_username(self.OWNER)
        process_client.ensure_reserved_username(self.READER_BY_USERNAME)
        process_client.ensure_reserved_username(self.READER_BY_ROLE)
        process_client.ensure_reserved_username(self.OTHER_USER)
        role_service_util.ensure_user_role(self.READER_BY_ROLE, self.ROLE)
        role_service_util.ensure_user_role(self.OTHER_USER, self.OTHER_ROLE)
        role_service_util.ensure_user_role(self.READER_BY_ROLE, self.NON_EXISTING_ROLE)
        for publication, access_rights, _ in self.PUBLICATIONS_DEFS:
            process_client.publish_workspace_publication(publication.type, publication.workspace, publication.name,
                                                         actor_name=self.OWNER, access_rights=access_rights, )
        role_service_util.delete_user_role(self.READER_BY_ROLE, self.NON_EXISTING_ROLE)
        role_service_util.delete_role(self.NON_EXISTING_ROLE)
        yield
        if request.node.session.testsfailed == 0 and not request.config.option.nocleanup:
            for publication, _, deleter in self.PUBLICATIONS_DEFS:
                process_client.delete_workspace_publication(publication.type, publication.workspace, publication.name,
                                                            actor_name=deleter, )
            role_service_util.delete_user_role(self.READER_BY_ROLE, self.ROLE)
            role_service_util.delete_role(self.ROLE)
            role_service_util.delete_user_role(self.OTHER_USER, self.OTHER_ROLE)
            role_service_util.delete_role(self.OTHER_ROLE)

    def test_single_positive(self, rest_method, rest_args, ):
        if rest_method is process_client.get_uuid_publication_thumbnail and rest_args.get('uuid') is None:
            with app.app_context():
                workspace = rest_args.pop('workspace')
                name = rest_args.pop('name')
                rest_args['uuid'] = get_publication_uuid(
                    workspace,
                    rest_args['publication_type'],
                    name,
                )
        accepted = inspect.signature(rest_method).parameters
        call_args = {k: v for k, v in rest_args.items() if k in accepted}
        rest_method(**call_args)

    def test_single_negative(self, rest_method, rest_args, ):
        if rest_method is process_client.get_uuid_publication_thumbnail and rest_args.get('uuid') is None:
            with app.app_context():
                workspace = rest_args.pop('workspace', None)
                name = rest_args.pop('name', None)
                if workspace and name:
                    rest_args['uuid'] = get_publication_uuid(
                        workspace,
                        rest_args['publication_type'],
                        name,
                    )
        accepted = inspect.signature(rest_method).parameters
        call_args = {k: v for k, v in rest_args.items() if k in accepted}
        with pytest.raises(LaymanError) as exc_info:
            rest_method(**call_args)
        assert exc_info.value.http_code == 404
        assert exc_info.value.code in [15, 26, ]

    def test_multiendpoint(self, rest_method, rest_args, params):
        result = rest_method(**rest_args)
        result_publications = [(publ['workspace'], f"layman.{publ['publication_type']}", publ['name']) for publ in result]
        assert result_publications == params['exp_publications']

    def test_geoserver_negative(self, rest_method, rest_args, ):
        with pytest.raises(AssertionError) as exc_info:
            rest_method(**rest_args)
        assert exc_info.value.args[0].startswith('Layer not found in Capabilities.')

    def test_wfst_positive(self, publication, rest_method, rest_args, params):
        attr_names = params.get('new_attributes', [])
        with app.app_context():
            layer = Layer(layer_tuple=(publication.workspace, publication.name))
            table_uri = layer.table_uri
            old_db_attributes = db.get_all_table_column_names(table_uri.schema, table_uri.table)
        for attr_name in attr_names:
            assert attr_name not in old_db_attributes, \
                f"old_db_attributes={old_db_attributes}, attr_name={attr_name}"
        rest_method(**rest_args)
        process_client.wait_for_publication_status(publication.workspace,
                                                   publication.type,
                                                   publication.name,
                                                   headers=params['headers'])
        assert_publ_util.is_publication_valid_and_complete(publication)
        with app.app_context():
            new_db_attributes = db.get_all_table_column_names(table_uri.schema, table_uri.table)
        for attr_name in attr_names:
            assert attr_name in new_db_attributes, \
                f"new_db_attributes={new_db_attributes}, attr_name={attr_name}"

    def test_wfst_negative(self, rest_method, rest_args, ):
        with pytest.raises(GS_Error) as exc_info:
            rest_method(**rest_args)
        assert exc_info.value.data['status_code'] == 400
