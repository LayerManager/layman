import inspect
import copy
import os
from typing import final, Tuple, Optional
import pytest

from tests.asserts.util import recursive_dict_update
from test_tools import process_client, cleanup, external_db
from .base_test_classes import WithChunksDomain, CompressDomainBase, CompressDomain, RestArgs, RestMethod, PublicationByDefinitionBase, \
    LayerByUsedServers, PublicationByUsedServers, TestCaseType, Parametrization, StyleFileDomainBase, RestMethodParam  # pylint: disable=unused-import
from . import base_test_util as util
from .base_test_classes import ExternalTableDef
from .. import Publication, EnumTestTypes, EnumTestKeys, PublicationValues


def pytest_generate_tests(metafunc):
    # used for parametrizing subclasses of TestSingleRestPublication, called once per each test function
    # https://docs.pytest.org/en/6.2.x/parametrize.html#pytest-generate-tests
    test_type_str = os.getenv(EnumTestKeys.TYPE.value) or EnumTestTypes.MANDATORY.value
    test_type = EnumTestTypes(test_type_str)
    cls = metafunc.cls
    test_fn = metafunc.function
    arg_names = [a for a in inspect.getfullargspec(test_fn).args if a != 'self']
    arg_names.append('post_before_test')
    publ_type_name = cls.publication_type.split('.')[-1] if cls.publication_type else 'publication'
    argvalues = []
    ids = []

    test_cases = cls.parametrize_test_cases()
    test_cases_for_type = [test_case for test_case in test_cases if
                           test_type == EnumTestTypes.OPTIONAL or test_case.type == EnumTestTypes.MANDATORY]
    for test_case in test_cases_for_type:
        assert not test_case.specific_params, f"Property specific_params is meant only for input test cases."
        assert not test_case.specific_types, f"Property specific_types is meant only for input test cases."
        assert not test_case.publication_type, f"Property publication_type is meant only for input test cases."
        assert test_case.type != EnumTestTypes.IGNORE, f"Test type IGNORE is meant only for input test cases."
        rest_method = getattr(cls, test_case.rest_method.function_name)
        rest_args = test_case.rest_args
        parametrization = test_case.parametrization
        arg_name_to_value = {
            publ_type_name: test_case.publication,
            'key': test_case.key,
            'params': copy.deepcopy(test_case.params),
            'rest_method': RestMethodParam(test_case.rest_method, rest_method),
            'rest_args': rest_args,
            'parametrization': parametrization,
            'post_before_test': (test_case.publication, test_case.rest_method, test_case.post_before_test_args),
        }
        arg_values = [arg_name_to_value[n] for n in arg_names]

        argvalues.append(pytest.param(*arg_values, marks=test_case.marks))
        ids.append(test_case.pytest_id)
    metafunc.parametrize(
        argnames=', '.join(arg_names),
        argvalues=argvalues,
        ids=ids,
        indirect=['post_before_test'],
    )


@pytest.mark.usefixtures('ensure_layman_module', 'ensure_external_db')
class TestSingleRestPublication:
    # pylint: disable=too-few-public-methods

    publications_to_cleanup_on_class_end = set()
    publications_to_cleanup_on_function_end = set()
    external_tables_to_cleanup_on_class_end = set()
    external_tables_to_cleanup_on_function_end = set()

    workspace = None

    publication_type = None

    test_cases = []

    rest_parametrization = []

    external_tables_to_create = []

    usernames_to_reserve = []

    post_before_test_scope = 'function'

    publ_uuids = {}

    @classmethod
    @final
    def parametrize_test_cases(cls) -> [TestCaseType]:
        util.check_rest_parametrization(cls.rest_parametrization)

        parametrizations = util.rest_parametrization_to_parametrizations(cls.rest_parametrization)
        util.check_input_test_cases(cls.test_cases, cls.rest_parametrization, parametrizations)

        test_cases = []
        for input_test_case in cls.test_cases:
            specific_types = util.dict_keys_to_simple_parametrizations(input_test_case.specific_types)
            specific_params = util.dict_keys_to_simple_parametrizations(input_test_case.specific_params)

            assert input_test_case.pytest_id is None  # Maybe enable it later

            for parametrization in parametrizations:
                test_type = specific_types.get(parametrization.values_set,
                                               input_test_case.type or EnumTestTypes.OPTIONAL)
                if test_type == EnumTestTypes.IGNORE:
                    continue

                publication_definition = parametrization.publication_definition

                specific_params_values = copy.deepcopy(specific_params.get(parametrization.values_set, {}))
                params = recursive_dict_update(copy.deepcopy(input_test_case.params), specific_params_values)

                input_publication, workspace, publication_type = cls._get_input_publication_workspace_and_type(
                    input_test_case=input_test_case, params=params, publication_definition=publication_definition,
                    parametrization=parametrization,
                )

                publ_name_parts = ([publication_type.split('.')[1]] if publication_type else []) + [
                    input_test_case.key.replace(':', '_').lower()
                ] + [
                    val.publ_name_part for val in parametrization.values_list if val.publ_name_part
                ]
                name = '_'.join(publ_name_parts)
                pytest_id = name

                if input_publication:
                    name = input_publication.name or name

                assert input_test_case.rest_method is None or parametrization.rest_method is None
                rest_method = parametrization.rest_method or input_test_case.rest_method or RestMethod.POST
                rest_args = copy.deepcopy(input_test_case.rest_args)
                if publication_definition:
                    rest_args.update(copy.deepcopy(publication_definition.definition))
                for base_arg, arg_value in parametrization.rest_arg_dict.items():
                    rest_args[base_arg.arg_name] = arg_value.raw_value
                    rest_args.update(copy.deepcopy(arg_value.other_rest_args))

                test_case = TestCaseType(pytest_id=pytest_id,
                                         publication=Publication(workspace, publication_type, name),
                                         key=input_test_case.key,
                                         rest_method=rest_method,
                                         rest_args=rest_args,
                                         post_before_test_args=input_test_case.post_before_test_args,
                                         params=params,
                                         type=test_type,
                                         marks=input_test_case.marks,
                                         parametrization=parametrization,
                                         )
                test_cases.append(test_case)
        return test_cases

    @classmethod
    @final
    def _get_input_publication_workspace_and_type(cls, *,
                                                  input_test_case: TestCaseType,
                                                  params: dict,
                                                  publication_definition: PublicationValues,
                                                  parametrization: Parametrization,
                                                  ) -> Tuple[Optional[Publication], str, str]:
        input_publication = None
        if isinstance(input_test_case.publication, Publication):
            input_publication = input_test_case.publication
        elif callable(input_test_case.publication):
            args_spec = inspect.getfullargspec(input_test_case.publication)
            arg_names_to_values = {
                'params': params,
                'publ_def': publication_definition,
                'cls': cls,
                'parametrization': parametrization,
            }
            args = [arg_names_to_values[n] for n in args_spec.args]
            input_publication = input_test_case.publication(*args)

        workspace = cls.workspace
        publication_type = input_test_case.publication_type or cls.publication_type

        if input_publication:
            workspace = input_publication.workspace or workspace
            publication_type = input_publication.type or publication_type
        return input_publication, workspace, publication_type

    @classmethod
    def post_publication(cls, publication, args=None, scope='function'):
        args = args or {}
        assert scope in {'function', 'class'}
        if scope == 'class':
            cls.publications_to_cleanup_on_class_end.add(publication)
        else:
            cls.publications_to_cleanup_on_function_end.add(publication)
        final_args = {
            'uuid': publication.uuid,
            **args,
        }

        resp = process_client.publish_workspace_publication(publication.type, publication.workspace, publication.name,
                                                            **final_args)
        if isinstance(resp, dict):
            maybe_uuid = resp.get('uuid', None)
            if maybe_uuid:
                cls.publ_uuids[publication] = maybe_uuid
        return resp

    @classmethod
    def ensure_publication(cls, publication, args=None, scope='function'):
        publ_set = cls.publications_to_cleanup_on_class_end if scope == 'class' else cls.publications_to_cleanup_on_function_end
        if publication not in publ_set:
            cls.post_publication(publication, args=args, scope=scope)

    @classmethod
    def import_external_table(cls, file_path, args=None, scope='function'):
        args = args or {}
        assert scope in {'function', 'class'}
        schema_table = external_db.import_table(file_path, **args)
        if scope == 'class':
            cls.external_tables_to_cleanup_on_class_end.add(schema_table)
        else:
            cls.external_tables_to_cleanup_on_function_end.add(schema_table)

    @classmethod
    def patch_publication(cls, publication, args=None):
        return process_client.patch_workspace_publication(publication.type, publication.workspace, publication.name, **args)

    @classmethod
    def delete_workspace_publication(cls, publication, args=None):
        return process_client.delete_workspace_publication(publication.type, publication.workspace, publication.name, **args)

    @classmethod
    def delete_workspace_publications(cls, publication, args=None):
        return process_client.delete_workspace_publications(publication.type, publication.workspace, **args)

    @pytest.fixture(scope='class', autouse=True)
    def class_fixture(self, request):
        for table in self.external_tables_to_create:
            assert isinstance(table, ExternalTableDef)
            self.import_external_table(table.file_path, {
                'schema': table.db_schema,
                'table': table.db_table,
                **(table.args or {}),
            }, scope='class')
        for username in self.usernames_to_reserve:
            process_client.ensure_reserved_username(username)
        self.before_class()
        yield
        self.after_class(request)

    def before_class(self):
        """Override to setup something before all tests in this class."""

    def after_class(self, request):
        """Override to clean up something after all tests in this class."""

    @pytest.fixture(scope='class', autouse=True)
    def class_cleanup(self, request):
        yield
        cleanup.cleanup_publications(request, self.publications_to_cleanup_on_class_end)
        self.publications_to_cleanup_on_class_end.clear()
        cleanup.cleanup_external_tables(request, self.external_tables_to_cleanup_on_class_end)
        self.external_tables_to_cleanup_on_class_end.clear()

    @pytest.fixture(scope='function', autouse=True)
    def function_cleanup(self, request):
        yield
        cleanup.cleanup_publications(request, self.publications_to_cleanup_on_function_end)
        self.publications_to_cleanup_on_function_end.clear()
        cleanup.cleanup_external_tables(request, self.external_tables_to_cleanup_on_function_end)
        self.external_tables_to_cleanup_on_function_end.clear()

    @pytest.fixture(scope='function', autouse=True)
    def post_before_test(self, request):
        if hasattr(request, 'param'):
            publication, method, post_before_test_args = request.param
            assert self.post_before_test_scope in {'function', 'class'}
            if method.name != RestMethod.POST.name:
                if self.post_before_test_scope == 'function':
                    self.post_publication(publication, args=post_before_test_args)
                else:
                    self.ensure_publication(publication, args=post_before_test_args, scope='class')
        yield
