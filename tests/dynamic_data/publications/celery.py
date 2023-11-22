from layman.common import empty_method_returns_true
from tests.asserts.final.publication import internal
from tests.asserts import processing
from test_tools import process_client, util
from ... import Action, Publication, dynamic_data as consts


def generate(workspace):
    return {
        Publication(workspace, consts.LAYER_TYPE, 'task_abortion'): [
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                        'file_paths': [
                            'tmp/naturalearth/10m/cultural/ne_10m_admin_0_countries.geojson',
                        ],
                        'check_response_fn': empty_method_returns_true,
                        'raise_if_not_complete': False,

                    }),
                    consts.KEY_RESPONSE_ASSERTS: [
                        Action(processing.response.valid_post, {}),
                    ],
                },
            },
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(util.sleep, {'seconds': 2}),
                },
            },
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(util.abort_publication_chain, {}),
                },
                consts.KEY_FINAL_ASSERTS: [
                    Action(internal.expected_chain_info_state, {'state': 'ABORTED'})
                ],
            }
        ],
    }
