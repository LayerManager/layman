import inspect
import pytest
from test_tools import process_client, process
from .. import dynamic_data as data


@pytest.fixture(scope="session", autouse=True)
def clear_test_data(liferay_mock, request):
    # pylint: disable=unused-argument
    yield

    if request.node.testsfailed == 0:
        process.ensure_layman_function(process.LAYMAN_DEFAULT_SETTINGS)

        for publication in data.PUBLICATIONS:
            process_client.delete_workspace_publication(publication.type, publication.workspace, publication.name, )


def run_action(publication, action):
    method_params = inspect.getfullargspec(action.method)
    publ_type_param = 'publication_type' if 'publication_type' in method_params[0] else 'publ_type'
    params = {
        publ_type_param: publication.type,
        'workspace': publication.workspace,
        'name': publication.name,
    }
    params.update(action.params)
    action.method(**params)


def publication_id(publication):
    return f'{publication.workspace}-{publication.type}-{publication.name}'


@pytest.mark.parametrize('publication', data.PUBLICATIONS, ids=publication_id)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_action_chain(publication):
    for step in data.PUBLICATIONS[publication]:
        action = step[data.KEY_ACTION]
        action_call = action[data.KEY_CALL]
        run_action(publication, action_call)

        for assert_call in step[data.KEY_FINAL_ASSERTS]:
            run_action(publication, assert_call)
