import tests.asserts.final.publication as publication
import tests.asserts.final.publication.internal
import tests.asserts.final.publication.internal_rest
import tests.asserts.final.publication.rest
import tests.asserts.final.publication.geoserver
from test_tools import process_client
from .. import Action, Publication


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
                Action(publication.internal.source_has_its_key_or_it_is_empty, dict()),
                Action(publication.internal.source_internal_keys_are_subset_of_source_sibling_keys, dict()),
                Action(publication.internal_rest.same_title_in_source_and_rest_multi, dict()),
                Action(publication.rest.is_in_rest_multi, dict()),
                Action(publication.rest.correct_url_in_rest_multi, dict()),
                Action(publication.internal.same_value_of_key_in_all_sources, dict()),
                Action(publication.internal.mandatory_keys_in_all_sources, dict()),
                Action(publication.internal.metadata_key_sources_do_not_contain_other_keys, dict()),
                Action(publication.internal.thumbnail_key_sources_do_not_contain_other_keys, dict()),
                Action(publication.internal.mandatory_keys_in_primary_db_schema_of_first_reader, dict()),
                Action(publication.internal.other_keys_not_in_primary_db_schema_of_first_reader, dict()),
                Action(publication.rest.is_complete_in_rest, dict()),
                Action(publication.rest.mandatory_keys_in_rest, dict()),
                Action(publication.geoserver.workspace_wms_1_3_0_capabilities_available, dict()),
                Action(publication.geoserver.workspace_wfs_2_0_0_capabilities_available_if_vector, dict()),
            ],
        },
    ],
}
