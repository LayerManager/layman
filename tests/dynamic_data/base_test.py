import inspect
import itertools
from enum import Enum
import copy
from dataclasses import dataclass, field
import os
from typing import final, List
import pytest
import _pytest.mark.structures
from test_tools import process_client, cleanup
from .. import Publication, EnumTestTypes, EnumTestKeys


class RestArgDomain(Enum):
    def __init__(self, raw_value, publ_name_part):
        self.raw_value = raw_value
        self.publ_name_part = publ_name_part


class WithChunksDomain(RestArgDomain):
    FALSE = (False, None)
    TRUE = (True, 'chunks')


class CompressDomain(RestArgDomain):
    FALSE = (False, None)
    TRUE = (True, 'zipped')


class RestArgs(Enum):
    WITH_CHUNKS = ('with_chunks', WithChunksDomain)
    COMPRESS = ('compress', CompressDomain)

    def __init__(self, name, domain):
        self.arg_name = name
        self.domain = domain


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
    publication: Publication = None
    key: str = None
    rest_method: RestMethod = None
    rest_args: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    type: EnumTestTypes = EnumTestTypes.OPTIONAL
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
    possible_dimensions = [RestMethod] + list(RestArgs)
    for val in cls.rest_parametrization:
        assert val in possible_dimensions, f"Only dimensions are allowed in cls.rest_parametrization. Found: {val}"


def check_input_test_cases(cls, parametrizations):
    for test_case in cls.test_cases:
        rest_args = test_case.rest_args
        for parametrization in parametrizations:
            for arg_value in [v for v in parametrization if v not in RestMethod]:
                arg = next(a for a in RestArgs if arg_value in a.domain)
                assert arg.arg_name not in rest_args, f"REST argument can be set either in parametrization or in test case, not both: {arg}, test_case={test_case.key}"


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

            for parametrization in parametrizations:
                workspace = cls.workspace
                publication_type = cls.publication_type

                if input_test_case.publication:
                    workspace = input_test_case.publication.workspace or workspace
                    publication_type = input_test_case.publication.type or publication_type
                publ_name_parts = [publication_type.split('.')[1], input_test_case.key.replace(':', '_').lower()] +\
                                  [p.publ_name_part for p in parametrization if p.publ_name_part]
                name = '_'.join(publ_name_parts)

                if input_test_case.publication:
                    name = input_test_case.publication.name or name

                rest_method = next(
                    (v for v in parametrization if v in RestMethod),
                    RestMethod.POST,
                )
                rest_args = copy.deepcopy(input_test_case.rest_args)
                for arg_value in [v for v in parametrization if v not in RestMethod]:
                    arg = next(a for a in RestArgs if arg_value in a.domain)
                    rest_args[arg.arg_name] = arg_value.raw_value

                test_case = TestCaseType(pytest_id=input_test_case.pytest_id or name,
                                         publication=Publication(workspace, publication_type, name),
                                         key=input_test_case.key,
                                         rest_method=rest_method,
                                         rest_args=rest_args,
                                         params=copy.deepcopy(input_test_case.params),
                                         type=input_test_case.type or EnumTestTypes.OPTIONAL,
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
