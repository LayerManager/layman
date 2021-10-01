from test_tools import process_client
from .. import Action, Publication
from ..asserts.final import publication

LAYER_TYPE = process_client.LAYER_TYPE
MAP_TYPE = process_client.MAP_TYPE

KEY_ACTION = 'action'
KEY_CALL = 'call'
KEY_FINAL_ASSERTS = 'final_asserts'

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
                Action(publication.same_title_in_source_and_rest_multi, dict()),
                Action(publication.is_in_rest_multi, dict()),
                Action(publication.correct_url_in_rest_multi, dict()),
                Action(publication.same_value_of_key_in_all_sources, dict()),
                Action(publication.mandatory_keys_in_all_sources, dict()),
                Action(publication.metadata_key_sources_do_not_contain_other_keys, dict()),
                Action(publication.thumbnail_key_sources_do_not_contain_other_keys, dict()),
                Action(publication.mandatory_keys_in_primary_db_schema_of_first_reader, dict()),
                Action(publication.other_keys_not_in_primary_db_schema_of_first_reader, dict()),
                Action(publication.is_complete_in_rest, dict()),
                Action(publication.mandatory_keys_in_rest, dict()),
                Action(publication.workspace_wms_1_3_0_capabilities_available, dict()),
                Action(publication.workspace_wfs_2_0_0_capabilities_available_if_vector, dict()),
            ],
        },
    ],
}
