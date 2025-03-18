from geoserver.error import Error as gs_error
from layman import settings
from layman.layer.geoserver import GEOSERVER_WFS_WORKSPACE
from tests.asserts.final import publication
from tests.asserts import processing
from test_tools import process_client, wfs_client
from . import common_publications as publications
from ... import Action, Publication4Test, dynamic_data as consts


def wfst_insert_action(*,
                       workspace=None,
                       headers=None,
                       wrong_input=False,
                       ):
    action = {
        consts.KEY_ACTION: {
            consts.KEY_CALL: Action(wfs_client.post_wfst, {
                'operation': wfs_client.WfstOperation.INSERT,
                'version': wfs_client.WfstVersion.WFS20,
                'request_workspace': workspace if workspace else None,
                'request_headers': headers if headers else None,
            }),
        },
        consts.KEY_FINAL_ASSERTS: [
            *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
        ],
    }
    if wrong_input:
        action[consts.KEY_ACTION][consts.KEY_CALL_EXCEPTION] = {
            consts.KEY_EXCEPTION: gs_error,
            consts.KEY_EXCEPTION_ASSERTS: [
                Action(processing.exception.response_exception,
                       {'expected': {'code': -1,
                                     'message': 'WFS-T error',
                                     'data': {
                                         'status_code': 400,
                                     },
                                     }, }, ),
            ],
        }
    return action


def generate(workspace):
    username = workspace + '_user'
    username_2 = workspace + '_user_2'
    return {
        Publication4Test(workspace, consts.LAYER_TYPE, 'layer_wfs_proxy'): [
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.publish_workspace_publication, publications.SMALL_LAYER.definition),
                    consts.KEY_RESPONSE_ASSERTS: [
                        Action(processing.response.valid_post, {}),
                    ],
                },
                consts.KEY_FINAL_ASSERTS: [
                    *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                    Action(publication.internal.correct_values_in_detail, publications.SMALL_LAYER.info_values),
                    Action(publication.internal.thumbnail_equals, {
                        'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
                    }),
                ],
            },
            wfst_insert_action(workspace=GEOSERVER_WFS_WORKSPACE),
            wfst_insert_action(),
        ],
        Publication4Test(workspace, consts.LAYER_TYPE, 'layer_wfs_proxy_authz'): [
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.ensure_reserved_username, {
                        'username': username,
                        'headers': process_client.get_authz_headers(username=username),
                    }),
                },
            },
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.ensure_reserved_username, {
                        'username': username_2,
                        'headers': process_client.get_authz_headers(username=username_2),
                    }),
                },
            },
            {
                consts.KEY_ACTION: {
                    consts.KEY_CALL: Action(process_client.publish_workspace_publication, {
                        **publications.SMALL_LAYER.definition,
                        'headers': process_client.get_authz_headers(username=username),
                    }),
                    consts.KEY_RESPONSE_ASSERTS: [
                        Action(processing.response.valid_post, {}),
                    ],
                },
                consts.KEY_FINAL_ASSERTS: [
                    *publication.IS_LAYER_COMPLETE_AND_CONSISTENT,
                    Action(publication.internal.correct_values_in_detail, {
                        **publications.SMALL_LAYER.info_values,
                        'exp_publication_detail': {**publications.SMALL_LAYER.info_values.get('exp_publication_detail', {}),
                                                   'access_rights': {'read': [username],
                                                                     'write': [username]},
                                                   }
                    }),
                    Action(publication.internal.thumbnail_equals, {
                        'exp_thumbnail': publications.SMALL_LAYER.thumbnail,
                    }),
                ],
            },
            wfst_insert_action(workspace=GEOSERVER_WFS_WORKSPACE,
                               headers=process_client.get_authz_headers(username=username)),
            wfst_insert_action(headers=process_client.get_authz_headers(username=username)),
            wfst_insert_action(workspace=GEOSERVER_WFS_WORKSPACE,
                               headers=process_client.get_authz_headers(username=username_2),
                               wrong_input=True,
                               ),
            wfst_insert_action(headers=process_client.get_authz_headers(username=username_2),
                               wrong_input=True,
                               ),
            wfst_insert_action(workspace=GEOSERVER_WFS_WORKSPACE,
                               wrong_input=True,
                               ),
            # Test fraud header, that it is deleted by Layman Proxy
            wfst_insert_action(headers={settings.LAYMAN_GS_AUTHN_HTTP_HEADER_ATTRIBUTE: username, },
                               wrong_input=True,
                               ),
        ],
    }
