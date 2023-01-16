import inspect
import itertools
from enum import Enum
import copy
from dataclasses import dataclass, field
import os
from typing import final, List, Union, Callable
import pytest
import _pytest.mark.structures
from test_tools import process_client, cleanup
from .. import Publication, EnumTestTypes, EnumTestKeys


class RestArgDomain(Enum):
    def __init__(self, raw_value, publ_name_part, other_rest_args=None):
        self.raw_value = raw_value
        self.publ_name_part = publ_name_part
        self.other_rest_args = other_rest_args or {}


class WithChunksDomain(RestArgDomain):
    FALSE = (False, None)
    TRUE = (True, 'chunks')


class CompressDomainBase(RestArgDomain):
    pass


class CompressDomain(CompressDomainBase):
    FALSE = (False, None)
    TRUE = (True, 'zipped')


class RestArgs(Enum):
    WITH_CHUNKS = ('with_chunks', WithChunksDomain)
    COMPRESS = ('compress', CompressDomain, CompressDomainBase)

    def __init__(self, name, domain, base_domain=None):
        self.arg_name = name
        self.domain = domain
        self.base_domain = base_domain or domain


class RestMethod(Enum):
    POST = ('post_publication', 'post')
    PATCH = ('patch_publication', 'patch')

    def __init__(self, function_name, publ_name_part):
        self.function_name = function_name
        self.publ_name_part = publ_name_part


def get_dimension_enum(dimension):
    return dimension if inspect.isclass(dimension) and issubclass(dimension, Enum) else dimension.domain


@dataclass(frozen=True)
class TestCaseType:
    pytest_id: str = None
    publication: Union[Publication, Callable[[dict], Publication]] = None
    key: str = None
    rest_method: RestMethod = None
    rest_args: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    specific_params: dict = field(default_factory=dict)
    type: EnumTestTypes = EnumTestTypes.OPTIONAL
    specific_types: dict = field(default_factory=dict)
    marks: List[_pytest.mark.structures.Mark] = field(default_factory=list)


def pytest_generate_tests(metafunc):
    # used for parametrizing subclasses of TestSingleRestPublication, called once per each test function
    # https://docs.pytest.org/en/6.2.x/parametrize.html#pytest-generate-tests
    test_type_str = os.getenv(EnumTestKeys.TYPE.value) or EnumTestTypes.MANDATORY.value
    test_type = EnumTestTypes(test_type_str)
    cls = metafunc.cls
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
        argvalues.append(pytest.param(
            test_case.publication,
            test_case.key,
            copy.deepcopy(test_case.params),
            rest_method,
            rest_args,
            (test_case.publication, test_case.rest_method),
            marks=test_case.marks,
        ))
        ids.append(test_case.pytest_id)
    publ_type_name = cls.publication_type.split('.')[-1] if cls.publication_type else 'publication'
    metafunc.parametrize(
        argnames=f'{publ_type_name}, key, params, rest_method, rest_args, post_before_patch',
        argvalues=argvalues,
        ids=ids,
        indirect=['post_before_patch'],
    )


def check_rest_parametrization(cls):
    for val in cls.rest_parametrization:
        simple_type = val == RestMethod or val in list(RestArgs)
        base_arg = inspect.isclass(val) and next((arg for arg in RestArgs if issubclass(val, arg.base_domain)), None)
        custom_type = not simple_type and base_arg
        assert simple_type or custom_type, f"Only dimensions are allowed in cls.rest_parametrization. Found: {val}"
        if (not simple_type) and custom_type:
            base_arg_domain_raw_values = set(v.raw_value for v in base_arg.domain)
            domain_raw_values = set(v.raw_value for v in val)
            assert domain_raw_values <= base_arg_domain_raw_values


def check_input_test_cases(cls, parametrizations):
    for test_case in cls.test_cases:
        if test_case.type:
            for parametrization, specific_type in test_case.specific_types.items():
                assert specific_type != test_case.type, f"No need to set specific test type that is same as main type: specific_type{specific_type}, type={test_case.type} test_case={test_case.key}"

        all_specific_parametrizations = set(test_case.specific_types.keys()).union(set(test_case.specific_params.keys()))
        for sp_parametrization in all_specific_parametrizations:
            assert len(sp_parametrization) == len(cls.rest_parametrization), f"Specific parametrization must have same number of members as cls.rest_paramertization"
            for dimension in cls.rest_parametrization:
                dimension_enum = get_dimension_enum(dimension)
                param_values = [v for v in sp_parametrization if v in dimension_enum]
                assert len(param_values) == 1, f"Specific parametrization {sp_parametrization} does not have value of dimension {dimension}"

        rest_args = test_case.rest_args
        for parametrization in parametrizations:
            for arg_value in [v for v in parametrization if v not in RestMethod]:
                base_arg = get_base_arg_of_arg_value(cls, arg_value)
                assert base_arg.arg_name not in rest_args, f"REST argument can be set either in parametrization or in test case, not both: {base_arg}, test_case={test_case.key}"


def get_base_arg_of_arg_value(cls, arg_value):
    dimension = next(dim for dim in cls.rest_parametrization if arg_value in get_dimension_enum(dim))
    domain = get_dimension_enum(dimension)
    base_arg = next(arg for arg in RestArgs if issubclass(domain, arg.base_domain))
    return base_arg


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
        check_rest_parametrization(cls)

        parametrization_values = []
        for dimension in cls.rest_parametrization:
            all_dim_values = list(get_dimension_enum(dimension))
            parametrization_values.append(all_dim_values)

        parametrizations = list(itertools.product(*parametrization_values)) or [[]]
        check_input_test_cases(cls, parametrizations)
        test_cases = []
        for input_test_case in cls.test_cases:
            assert input_test_case.rest_method is None  # Maybe enable it later
            assert input_test_case.pytest_id is None  # Maybe enable it later

            for parametrization in parametrizations:
                test_type = input_test_case.specific_types.get(frozenset(parametrization),
                                                               input_test_case.type or EnumTestTypes.OPTIONAL)
                if test_type == EnumTestTypes.IGNORE:
                    continue

                specific_params = copy.deepcopy(input_test_case.specific_params.get(frozenset(parametrization), {}))
                params = {**copy.deepcopy(input_test_case.params), **specific_params}
                input_publication = None
                if isinstance(input_test_case.publication, Publication):
                    input_publication = input_test_case.publication
                elif callable(input_test_case.publication):
                    input_publication = input_test_case.publication(params)

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
                rest_args = copy.deepcopy(input_test_case.rest_args)
                for arg_value in [v for v in parametrization if v not in RestMethod]:
                    base_arg = get_base_arg_of_arg_value(cls, arg_value)
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
