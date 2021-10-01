from collections import namedtuple
from test_tools import process_client
from ..asserts.final import publication

LAYER_TYPE = process_client.LAYER_TYPE
MAP_TYPE = process_client.MAP_TYPE

KEY_ACTION = 'action'
KEY_CALL = 'call'
KEY_FINAL_ASSERTS = 'final_asserts'

Action = namedtuple('ActionTypeDef', ['method', 'params', ])
Publication = namedtuple('PublicationTypeDef', ['workspace', 'type', 'name'])

COMMON_WORKSPACE = 'dynamic_test_workspace'

PUBLICATIONS = {
    Publication(COMMON_WORKSPACE, LAYER_TYPE, 'basic_sld'): [
        {
            KEY_ACTION: {
                KEY_CALL: Action(process_client.publish_workspace_publication, dict()),
            },
            KEY_FINAL_ASSERTS: [
                Action(publication.source_has_its_key_or_it_is_empty, dict()),
                Action(publication.source_internal_keys_are_subset_of_source_sibling_keys, dict()),
            ],
        },
    ],
}
