import inspect
import itertools
import copy
import os
from typing import final
import pytest
from test_tools import process_client, cleanup
from .base_test_classes import WithChunksDomain, CompressDomainBase, CompressDomain, RestArgs, RestMethod, PublicationByDefinitionBase, \
    LayerByUsedServers, PublicationByUsedServers, TestCaseType, Parametrization  # pylint: disable=unused-import
from . import base_test_util as util
from .. import Publication, EnumTestTypes, EnumTestKeys


def pytest_generate_tests(metafunc):
    # used for parametrizing subclasses of TestSingleRestPublication, called once per each test function
    # https://docs.pytest.org/en/6.2.x/parametrize.html#pytest-generate-tests
    test_type_str = os.getenv(EnumTestKeys.TYPE.value) or EnumTestTypes.MANDATORY.value
    test_type = EnumTestTypes(test_type_str)
    cls = metafunc.cls
    test_fn = metafunc.function
    arg_names = [a for a in inspect.getfullargspec(test_fn).args if a != 'self']
    arg_names.append('post_before_patch')
    publ_type_name = cls.publication_type.split('.')[-1] if cls.publication_type else 'publication'
    argvalues = []
    ids = []

    test_cases = cls.parametrize_test_cases()
    test_cases_for_type = [test_case for test_case in test_cases if
                           test_type == EnumTestTypes.OPTIONAL or test_case.type == EnumTestTypes.MANDATORY]
    for test_case in test_cases_for_type:
        assert not test_case.specific_params
        assert not test_case.specific_types
        assert test_case.type != EnumTestTypes.IGNORE
        rest_method = getattr(cls, test_case.rest_method.function_name)
        rest_args = test_case.rest_args
        parametrization = test_case.parametrization
        wanted_arg_name_to_value = {
            publ_type_name: test_case.publication,
            'key': test_case.key,
            'params': copy.deepcopy(test_case.params),
            'rest_method': rest_method,
            'rest_args': rest_args,
            'parametrization': parametrization,
            'post_before_patch': (test_case.publication, test_case.rest_method),
        }
        arg_values = [wanted_arg_name_to_value[n] for n in arg_names]

        argvalues.append(pytest.param(*arg_values, marks=test_case.marks))
        ids.append(test_case.pytest_id)
    metafunc.parametrize(
        argnames=', '.join(arg_names),
        argvalues=argvalues,
        ids=ids,
        indirect=['post_before_patch'],
    )


@pytest.mark.usefixtures('ensure_layman_module')
class TestSingleRestPublication:
    # pylint: disable=too-few-public-methods

    publications_to_cleanup_on_class_end = set()
    publications_to_cleanup_on_function_end = set()

    workspace = None

    publication_type = None

    test_cases = []

    rest_parametrization = {
        RestMethod,  # parametrize with all values, i.e. PATCH and POST
    }

    @classmethod
    @final
    def parametrize_test_cases(cls) -> [TestCaseType]:
        util.check_rest_parametrization(cls)

        parametrization_values = []
        for dimension in cls.rest_parametrization:
            all_dim_values = list(util.get_dimension_enum(dimension))
            parametrization_values.append(all_dim_values)

        parametrizations = list(itertools.product(*parametrization_values)) or [[]]
        util.check_input_test_cases(cls, parametrizations)
        test_cases = []
        for input_test_case in cls.test_cases:
            assert input_test_case.rest_method is None  # Maybe enable it later
            assert input_test_case.pytest_id is None  # Maybe enable it later

            for parametrization in parametrizations:
                test_type = input_test_case.specific_types.get(frozenset(parametrization),
                                                               input_test_case.type or EnumTestTypes.OPTIONAL)
                if test_type == EnumTestTypes.IGNORE:
                    continue

                param_inst = Parametrization(parametrization, rest_parametrization=cls.rest_parametrization)
                publication_definition = param_inst.publication_definition

                specific_params = copy.deepcopy(input_test_case.specific_params.get(frozenset(parametrization), {}))
                params = {**copy.deepcopy(input_test_case.params), **specific_params}

                input_publication = None
                if isinstance(input_test_case.publication, Publication):
                    input_publication = input_test_case.publication
                elif callable(input_test_case.publication):
                    args_spec = inspect.getfullargspec(input_test_case.publication)
                    arg_names_to_values = {
                        'params': params,
                        'publ_def': publication_definition,
                        'cls': cls,
                    }
                    args = [arg_names_to_values[n] for n in args_spec.args]
                    input_publication = input_test_case.publication(*args)

                workspace = cls.workspace
                publication_type = cls.publication_type

                if input_publication:
                    workspace = input_publication.workspace or workspace
                    publication_type = input_publication.type or publication_type
                publ_name_parts = [publication_type.split('.')[1], input_test_case.key.replace(':', '_').lower()] +\
                                  [p.publ_name_part for p in parametrization if p.publ_name_part]
                name = '_'.join(publ_name_parts)
                pytest_id = name

                if input_publication:
                    name = input_publication.name or name

                rest_method = next(
                    (v for v in parametrization if v in RestMethod),
                    RestMethod.POST,
                )
                if publication_definition:
                    rest_args = copy.deepcopy(publication_definition.definition)
                else:
                    rest_args = copy.deepcopy(input_test_case.rest_args)
                    for arg_value in [v for v in parametrization if v not in RestMethod]:
                        base_arg = util.get_base_arg_of_value(cls.rest_parametrization, arg_value)
                        rest_args[base_arg.arg_name] = arg_value.raw_value
                        rest_args.update(copy.deepcopy(arg_value.other_rest_args))

                test_case = TestCaseType(pytest_id=pytest_id,
                                         publication=Publication(workspace, publication_type, name),
                                         key=input_test_case.key,
                                         rest_method=rest_method,
                                         rest_args=rest_args,
                                         params=params,
                                         type=test_type,
                                         marks=input_test_case.marks,
                                         parametrization=param_inst,
                                         )
                test_cases.append(test_case)
        return test_cases

    @classmethod
    def post_publication(cls, publication, args=None, scope='function'):
        args = args or {}
        assert scope in {'function', 'class'}
        if scope == 'class':
            cls.publications_to_cleanup_on_class_end.add(publication)
        else:
            cls.publications_to_cleanup_on_function_end.add(publication)

        process_client.publish_workspace_publication(publication.type, publication.workspace, publication.name,
                                                     **args)

    @classmethod
    def patch_publication(cls, publication, args=None):
        process_client.patch_workspace_publication(publication.type, publication.workspace, publication.name, **args)

    @pytest.fixture(scope='class', autouse=True)
    def class_fixture(self):
        self.before_class()
        yield

    def before_class(self):
        """Override to setup something before all tests in this class."""

    @pytest.fixture(scope='class', autouse=True)
    def class_cleanup(self, request):
        yield
        cleanup.cleanup_publications(request, self.publications_to_cleanup_on_class_end)
        self.publications_to_cleanup_on_class_end.clear()

    @pytest.fixture(scope='function', autouse=True)
    def function_cleanup(self, request):
        yield
        cleanup.cleanup_publications(request, self.publications_to_cleanup_on_function_end)
        self.publications_to_cleanup_on_function_end.clear()

    @pytest.fixture(scope='function', autouse=True)
    def post_before_patch(self, request):
        publication, method = request.param
        if method == RestMethod.PATCH:
            # currently, it posts default layer or map
            self.post_publication(publication)
        yield
