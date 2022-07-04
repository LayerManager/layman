from collections import namedtuple
import copy
from dataclasses import dataclass, field
import os
from typing import final
import pytest
from test_tools import process_client, cleanup
from .. import Publication, TestTypes, TestKeys

RestMethodType = namedtuple('RestMethodTypeDef', ['function_name', 'name'])


@dataclass(frozen=True)
class TestCaseType:
    pytest_id: str = None
    publication: Publication = None
    key: str = None
    method: RestMethodType = None
    params: dict = field(default_factory=dict)
    type: TestTypes = TestTypes.OPTIONAL


def pytest_generate_tests(metafunc):
    # used for parametrizing subclasses of TestSingleRestPublication, called once per each test function
    # https://docs.pytest.org/en/6.2.x/parametrize.html#pytest-generate-tests
    test_type_str = os.getenv(TestKeys.TYPE.value, TestTypes.MANDATORY.value)
    test_type = TestTypes(test_type_str)
    cls = metafunc.cls
    argvalues = []
    ids = []

    test_cases = cls.parametrize_test_cases()
    test_cases_for_type = [test_case for test_case in test_cases if
                           test_type == TestTypes.OPTIONAL or test_case.type == TestTypes.MANDATORY]
    for test_case in test_cases_for_type:
        rest_method = getattr(cls, test_case.method.function_name)
        argvalues.append([
            test_case.publication,
            test_case.key,
            copy.deepcopy(test_case.params),
            rest_method,
            (test_case.publication, test_case.method.name),
        ])
        ids.append(test_case.pytest_id)
    publ_type_name = cls.publication_type.split('.')[-1] if cls.publication_type else 'publication'
    metafunc.parametrize(
        argnames=f'{publ_type_name}, key, params, rest_method, post_before_patch',
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
        'method': [
            RestMethodType('post_publication', 'post'),
            RestMethodType('patch_publication', 'patch'),
        ],
    }

    @classmethod
    @final
    def parametrize_test_cases(cls) -> [TestCaseType]:
        test_cases = []
        for input_test_case in cls.test_cases:
            for rest_method in cls.rest_parametrization['method']:
                workspace = cls.workspace
                publication_type = cls.publication_type

                if input_test_case.publication:
                    workspace = input_test_case.publication.workspace or workspace
                    publication_type = input_test_case.publication.type or publication_type
                name = f"{publication_type.split('.')[1]}_{input_test_case.key.replace(':', '_').lower()}_{rest_method.name}"

                if input_test_case.publication:
                    name = input_test_case.publication.name or name

                test_case = TestCaseType(pytest_id=input_test_case.pytest_id or name,
                                         publication=Publication(workspace, publication_type, name),
                                         key=input_test_case.key,
                                         method=rest_method,
                                         params=copy.deepcopy(input_test_case.params),
                                         type=input_test_case.type or TestTypes.OPTIONAL,
                                         )
                test_cases.append(test_case)
        return test_cases

    @classmethod
    def post_publication(cls, publication, params=None, scope='function'):
        params = params or {}
        assert scope in {'function', 'class'}
        if scope == 'class':
            cls.publications_to_cleanup_on_class_end.add(publication)
        else:
            cls.publications_to_cleanup_on_function_end.add(publication)

        process_client.publish_workspace_publication(publication.type, publication.workspace, publication.name,
                                                     **params)

    @classmethod
    def patch_publication(cls, publication, params=None):
        process_client.patch_workspace_publication(publication.type, publication.workspace, publication.name, **params)

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
        if method == 'patch':
            # currently, it posts default layer or map
            self.post_publication(publication)
        yield
