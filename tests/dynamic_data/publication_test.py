from contextlib import nullcontext as does_not_raise
import pytest

from test_tools import cleanup
from . import publications as data
from ..asserts import util
from .. import Action, dynamic_data as consts


def publication_id(publication):
    return f'{publication.workspace}-{publication.type}-{publication.name}'


@pytest.mark.timeout(60)
@pytest.mark.parametrize('publication', data.PUBLICATIONS, ids=publication_id)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_action_chain(publication, request):
    for action_idx, step in enumerate(data.PUBLICATIONS[publication]):
        response = None
        action = step[consts.KEY_ACTION]
        exp_exception = pytest.raises(action[consts.KEY_CALL_EXCEPTION][consts.KEY_EXCEPTION]) if consts.KEY_CALL_EXCEPTION in action else does_not_raise()
        with exp_exception as exception_info:
            action_call = action[consts.KEY_CALL]
            response = util.run_action(publication, action_call)
        exception_assert_param = {'thrown': exception_info}
        for assert_call in action.get(consts.KEY_CALL_EXCEPTION, {}).get(consts.KEY_EXCEPTION_ASSERTS, []):
            params = dict(**exception_assert_param, **assert_call.params)
            util.run_action(publication, Action(assert_call.method, params))

        if not exception_info:
            response_assert_param = {'response': response}
            for response_assert_idx, assert_response in enumerate(action.get(consts.KEY_RESPONSE_ASSERTS, [])):
                params = dict(**response_assert_param, **assert_response.params)
                try:
                    util.run_action(publication, Action(assert_response.method, params))
                except AssertionError as exc:
                    print(
                        f'Response assert error raised: publication={publication}, action_idx={action_idx}, response_assert_idx={response_assert_idx}, assert_response={assert_response}')
                    raise exc from exc

        data_cache = {}
        for final_assert_idx, assert_call in enumerate(step.get(consts.KEY_FINAL_ASSERTS, [])):
            try:
                util.run_action(publication, assert_call, cache=data_cache)
            except AssertionError as exc:
                print(
                    f'Final assert error raised: publication={publication}, action_idx={action_idx}, final_assert_idx={final_assert_idx}, assert_call={assert_call}')
                raise exc from exc

    cleanup.cleanup_publications(request, [publication])
