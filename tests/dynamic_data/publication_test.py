from contextlib import nullcontext as does_not_raise
import pytest

from test_tools import process_client, process
from ..asserts import util
from .. import Action, dynamic_data as data


@pytest.fixture(scope="session", autouse=True)
def clear_test_data(liferay_mock, request):
    # pylint: disable=unused-argument
    yield

    if request.node.testsfailed == 0:
        process.ensure_layman_function(process.LAYMAN_DEFAULT_SETTINGS)

        for publication in data.PUBLICATIONS:
            headers = util.get_publication_header(publication)
            process_client.delete_workspace_publication(publication.type, publication.workspace, publication.name, headers=headers)


def publication_id(publication):
    return f'{publication.workspace}-{publication.type}-{publication.name}'


@pytest.mark.parametrize('publication', data.PUBLICATIONS, ids=publication_id)
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman')
def test_action_chain(publication):
    for step in data.PUBLICATIONS[publication]:
        response = None
        action = step[data.KEY_ACTION]
        exp_exception = pytest.raises(action[data.KEY_CALL_EXCEPTION][data.KEY_EXCEPTION]) if data.KEY_CALL_EXCEPTION in action else does_not_raise()
        with exp_exception as exception_info:
            action_call = action[data.KEY_CALL]
            response = util.run_action(publication, action_call)
        exception_assert_param = {'thrown': exception_info}
        for assert_call in action.get(data.KEY_CALL_EXCEPTION, dict()).get(data.KEY_EXCEPTION_ASSERTS, list()):
            params = dict(**exception_assert_param, **assert_call.params)
            util.run_action(publication, Action(assert_call.method, params))

        if not exception_info:
            response_assert_param = {'response': response}
            for assert_response in action.get(data.KEY_RESPONSE_ASSERTS, list()):
                params = dict(**response_assert_param, **assert_response.params)
                util.run_action(publication, Action(assert_response.method, params))

        data_cache = dict()
        for assert_call in step[data.KEY_FINAL_ASSERTS]:
            util.run_action(publication, assert_call, cache=data_cache)
