import copy
import os
import pytest
from test_tools import process_client, cleanup
from .. import Publication, TestTypes, TestKeys


def pytest_generate_tests(metafunc):
    # used for parametrizing subclasses of TestSingleRestPublication, called once per each test function
    # https://docs.pytest.org/en/6.2.x/parametrize.html#pytest-generate-tests
    test_type_str = os.getenv(TestKeys.TYPE.value, TestTypes.MANDATORY.value)
    test_type = TestTypes(test_type_str)
    cls = metafunc.cls
    rest_methods = cls.rest_parametrization['method']
    argvalues = []
    ids = []

    test_cases_for_type = {key: params for key, params in cls.test_cases.items() if
                           test_type == TestTypes.OPTIONAL or params.get(TestKeys.TYPE, cls.default_test_type) == TestTypes.MANDATORY}
    for key, params in test_cases_for_type.items():
        for method_function_name, method_name in rest_methods.items():
            publ_name = cls.key_to_publication_base_name(key) + f"_{method_name}"
            publication = Publication(cls.workspace, cls.publication_type, publ_name)
            rest_method = getattr(cls, method_function_name)
            argvalues.append([
                publication,
                key,
                copy.deepcopy(params),
                rest_method,
                (publication, method_name),
            ])
            ids.append(publ_name)
    publ_type_name = cls.publication_type.split('.')[-1]
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

    test_cases = dict()

    rest_parametrization = {
        'method': {
            'post_publication': 'post',
            'patch_publication': 'patch',
        },
    }

    default_test_type = TestTypes.OPTIONAL

    @classmethod
    def key_to_publication_base_name(cls, key):
        return f"{cls.publication_type.split('.')[1]}_{key.replace(':', '_').lower()}"

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
