import copy
import inspect
import pytest

from layman import settings, LaymanError
from test_tools import process_client, role_service as role_service_util
from tests import Publication, EnumTestTypes
from tests.dynamic_data import base_test

ENDPOINTS_TO_TEST = {
    process_client.LAYER_TYPE: [
        (process_client.get_workspace_publication, {}),
        (process_client.get_workspace_publication_metadata_comparison, {}),
        (process_client.get_workspace_layer_style, {}),
        (process_client.get_workspace_publication_thumbnail, {}),
        # process_client.get_workspace_layer_chunk,
        (process_client.patch_workspace_publication, {'title': 'New title'}),
        (process_client.patch_workspace_publication, {'file_paths': ['sample/layman.layer/small_layer.geojson']}),
    ],
    process_client.MAP_TYPE: [
        (process_client.get_workspace_publication, {}),
        (process_client.get_workspace_map_file, {}),
        (process_client.get_workspace_publication_metadata_comparison, {}),
        (process_client.get_workspace_publication_thumbnail, {}),
    ],
}


def pytest_generate_tests(metafunc):
    # https://docs.pytest.org/en/6.2.x/parametrize.html#pytest-generate-tests
    cls = metafunc.cls
    test_fn = metafunc.function
    arg_names = [a for a in inspect.getfullargspec(test_fn).args if a != 'self']
    argvalues = []
    ids = []

    test_cases = cls.test_cases[test_fn.__name__]
    for test_case in test_cases:
        assert not test_case.publication, f"Not yet implemented"
        assert not test_case.publication_type, f"Not yet implemented"
        assert not test_case.key, f"Not yet implemented"
        assert not test_case.specific_params, f"Not yet implemented"
        assert not test_case.specific_types, f"Not yet implemented"
        assert not test_case.parametrization, f"Not yet implemented"
        assert not test_case.post_before_test_args, f"Not yet implemented"
        assert test_case.type == EnumTestTypes.MANDATORY, f"Other types then MANDATORY are not implemented yet"
        arg_name_to_value = {
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
        'layer': publication.name,
        'actor_name': user,
        'publication_type': publication.type,
    }
    for method, args in endpoints_to_test[publication.type]:
        pytest_id = f'{method.__name__}__{user.split("_")[-1]}__{publication.name[5:]}{("__" + next(iter(args.keys()))) if args else ""}'
        method_args = inspect.getfullargspec(method).args + inspect.getfullargspec(method).kwonlyargs

        test_case = base_test.TestCaseType(pytest_id=pytest_id,
                                           rest_method=method,
                                           rest_args={**args, **{
                                               key: value for key, value in all_args.items() if key in method_args
                                           }},
                                           type=EnumTestTypes.MANDATORY,
                                           )

        tc_list.append(test_case)


def generate_positive_test_cases(publications_user_can_read):
    tc_list = []
    for user, publications in publications_user_can_read.items():
        for publication in publications:
            add_publication_test_cases_to_list(tc_list, publication, user, ENDPOINTS_TO_TEST)
    return tc_list


def generate_negative_test_cases(publications_user_can_read, publication_all):
    tc_list = []
    for user, available_publications in publications_user_can_read.items():
        for publication in publication_all:
            if publication in available_publications:
                continue
            add_publication_test_cases_to_list(tc_list, publication, user, ENDPOINTS_TO_TEST)
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
                                               type=EnumTestTypes.MANDATORY,
                                               )

            tc_list.append(test_case)
    return tc_list


@pytest.mark.timeout(60)
@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
class TestAccessRights:
    OWNER = 'test_access_rights_application_owner'
    READER = 'test_access_rights_application_reader'
    OTHER_USER = 'test_access_rights_application_other_user'
    ROLE = 'TEST_ACCESS_RIGHTS_APPLICATION_ROLE'
    OTHER_ROLE = 'TEST_ACCESS_RIGHTS_APPLICATION_OTHER_ROLE'
    NON_EXISTING_ROLE = 'TEST_ACCESS_RIGHTS_NON_EXISTING_ROLE'

    LAYER_NO_ACCESS = Publication(OWNER, process_client.LAYER_TYPE, 'test_no_access_layer')
    LAYER_USER_ACCESS = Publication(OWNER, process_client.LAYER_TYPE, 'test_user_access_layer')
    LAYER_ROLE_ACCESS = Publication(OWNER, process_client.LAYER_TYPE, 'test_role_access_layer')
    LAYER_EVERYONE_ACCESS = Publication(OWNER, process_client.LAYER_TYPE, 'test_everyone_access_layer')
    MAP_NO_ACCESS = Publication(OWNER, process_client.MAP_TYPE, 'test_no_access_map')
    MAP_USER_ACCESS = Publication(OWNER, process_client.MAP_TYPE, 'test_user_access_map')
    MAP_ROLE_ACCESS = Publication(OWNER, process_client.MAP_TYPE, 'test_role_access_map')
    MAP_EVERYONE_ACCESS = Publication(OWNER, process_client.MAP_TYPE, 'test_everyone_access_map')

    ACCESS_RIGHT_NO_ACCESS = {
        'read': OWNER,
        'write': OWNER,
    }
    ACCESS_RIGHTS_USER_ACCESS = {
        'read': f'{OWNER}, {READER}',
        'write': f'{OWNER}, {READER}',
    }
    ACCESS_RIGHTS_ROLE_ACCESS = {
        'read': f'{OWNER}, {ROLE}, {NON_EXISTING_ROLE}',
        'write': f'{OWNER}, {ROLE}, {NON_EXISTING_ROLE}',
    }
    ACCESS_RIGHTS_EVERYONE_ACCESS = {
        'read': settings.RIGHTS_EVERYONE_ROLE,
        'write': settings.RIGHTS_EVERYONE_ROLE,
    }

    PUBLICATIONS_DEFS = [
        (LAYER_NO_ACCESS, ACCESS_RIGHT_NO_ACCESS),
        (LAYER_USER_ACCESS, ACCESS_RIGHTS_USER_ACCESS),
        (LAYER_ROLE_ACCESS, ACCESS_RIGHTS_ROLE_ACCESS),
        (LAYER_EVERYONE_ACCESS, ACCESS_RIGHTS_EVERYONE_ACCESS),
        (MAP_NO_ACCESS, ACCESS_RIGHT_NO_ACCESS),
        (MAP_USER_ACCESS, ACCESS_RIGHTS_USER_ACCESS),
        (MAP_ROLE_ACCESS, ACCESS_RIGHTS_ROLE_ACCESS),
        (MAP_EVERYONE_ACCESS, ACCESS_RIGHTS_EVERYONE_ACCESS),
    ]

    PUBLICATIONS = [publication for publication, _ in PUBLICATIONS_DEFS]

    PUBLICATIONS_BY_USER = {
        OWNER: [publication for publication, _ in PUBLICATIONS_DEFS],
        READER: [LAYER_USER_ACCESS, LAYER_ROLE_ACCESS, LAYER_EVERYONE_ACCESS, MAP_USER_ACCESS, MAP_ROLE_ACCESS, MAP_EVERYONE_ACCESS, ],
        OTHER_USER: [LAYER_EVERYONE_ACCESS, MAP_EVERYONE_ACCESS, ],
        settings.ANONYM_USER: [LAYER_EVERYONE_ACCESS, MAP_EVERYONE_ACCESS, ],
    }

    test_cases = {
        'test_single_positive': generate_positive_test_cases(PUBLICATIONS_BY_USER),
        'test_single_negative': generate_negative_test_cases(PUBLICATIONS_BY_USER, PUBLICATIONS),
        'test_multiendpoint': generate_multiendpoint_test_cases(PUBLICATIONS_BY_USER, OWNER),
    }

    @pytest.fixture(scope='class', autouse=True)
    def class_fixture(self, request):
        process_client.ensure_reserved_username(self.OWNER, process_client.get_authz_headers(self.OWNER))
        process_client.ensure_reserved_username(self.READER, process_client.get_authz_headers(self.READER))
        process_client.ensure_reserved_username(self.OTHER_USER, process_client.get_authz_headers(self.OTHER_USER))
        role_service_util.ensure_user_role(self.READER, self.ROLE)
        role_service_util.ensure_user_role(self.OTHER_USER, self.OTHER_ROLE)
        role_service_util.ensure_user_role(self.READER, self.NON_EXISTING_ROLE)
        for publication, access_rights in self.PUBLICATIONS_DEFS:
            process_client.publish_workspace_publication(publication.type, publication.workspace, publication.name,
                                                         actor_name=self.OWNER, access_rights=access_rights, )
        role_service_util.delete_user_role(self.READER, self.NON_EXISTING_ROLE)
        role_service_util.delete_role(self.NON_EXISTING_ROLE)
        yield
        if request.node.session.testsfailed == 0 and not request.config.option.nocleanup:
            for publication, access_rights in self.PUBLICATIONS_DEFS:
                process_client.delete_workspace_publication(publication.type, publication.workspace, publication.name,
                                                            actor_name=self.OWNER, )
            role_service_util.delete_user_role(self.READER, self.ROLE)
            role_service_util.delete_role(self.ROLE)
            role_service_util.delete_user_role(self.OTHER_USER, self.OTHER_ROLE)
            role_service_util.delete_role(self.OTHER_ROLE)

    def test_single_positive(self, rest_method, rest_args, ):
        rest_method(**rest_args)

    def test_single_negative(self, rest_method, rest_args, ):
        with pytest.raises(LaymanError) as exc_info:
            rest_method(**rest_args)
        assert exc_info.value.http_code == 404
        assert exc_info.value.code in [15, 26, ]

    def test_multiendpoint(self, rest_method, rest_args, params):
        result = rest_method(**rest_args)
        result_publications = [(publ['workspace'], f"layman.{publ['publication_type']}", publ['name']) for publ in result]
        assert result_publications == params['exp_publications']
