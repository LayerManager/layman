import tests.asserts.final.publication as publication
import tests.asserts.processing as processing
from test_tools import process_client, wfs_client
from . import common_layers as layers
from ... import Action, Publication, dynamic_data as consts


def generate(workspace):
    return {
        Publication(workspace, consts.LAYER_TYPE, 'layer_wfs_proxy'): [
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.publish_workspace_publication, layers.SMALL_LAYER.definition),
                    consts.KEY_RESPONSE_ASSERTS: [
                        Action(processing.response.valid_post, dict()),
                    ],
                },
                consts.KEY_FINAL_ASSERTS: [
                    *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                    Action(publication.internal.correct_values_in_detail, layers.SMALL_LAYER.info_values),
                    Action(publication.internal.thumbnail_equals, {
                        'exp_thumbnail': layers.SMALL_LAYER.thumbnail,
                    }),
                ],
            },
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(wfs_client.post_wfst, {
                        'operation': wfs_client.WfstOperation.INSERT,
                        'version': wfs_client.WfstVersion.WFS20,
                        'request_workspace': workspace,
                    }),
                },
            },
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(wfs_client.post_wfst, {
                        'operation': wfs_client.WfstOperation.INSERT,
                        'version': wfs_client.WfstVersion.WFS20,
                    }),
                },
            },
        ],
    }
