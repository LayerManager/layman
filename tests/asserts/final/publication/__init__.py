from tests import Action
from test_tools import process_client
from . import geoserver, internal, internal_rest, rest


IS_LAYER_COMPLETE_AND_CONSISTENT = [
    Action(internal.source_has_its_key_or_it_is_empty, dict()),
    Action(internal.source_internal_keys_are_subset_of_source_sibling_keys, dict()),
    Action(internal_rest.same_title_in_source_and_rest_multi, dict()),
    Action(internal_rest.same_values_in_internal_and_rest, dict()),
    Action(rest.is_in_rest_multi, dict()),
    Action(rest.correct_url_in_rest_multi, dict()),
    Action(internal.same_value_of_key_in_all_sources, dict()),
    Action(internal.mandatory_keys_in_all_sources, dict()),
    Action(internal.all_keys_assigned_to_source, dict()),
    Action(internal.metadata_key_sources_do_not_contain_other_keys, dict()),
    Action(internal.thumbnail_key_sources_do_not_contain_other_keys, dict()),
    Action(internal.mandatory_keys_in_primary_db_schema_of_actor, dict()),
    Action(internal.other_keys_not_in_primary_db_schema_of_actor, dict()),
    Action(internal.mandatory_keys_in_all_sources_of_actor, dict()),
    Action(internal.nodata_preserved_in_normalized_raster, dict()),
    Action(rest.is_complete_in_rest, dict()),
    Action(rest.mandatory_keys_in_rest, dict()),
    Action(geoserver.workspace_wms_1_3_0_capabilities_available, dict()),
    Action(geoserver.workspace_wfs_2_0_0_capabilities_available_if_vector, dict()),
]

IS_MAP_COMPLETE_AND_CONSISTENT = [
    Action(internal.source_has_its_key_or_it_is_empty, dict()),
    Action(internal.source_internal_keys_are_subset_of_source_sibling_keys, dict()),
    Action(internal_rest.same_title_in_source_and_rest_multi, dict()),
    Action(internal_rest.same_values_in_internal_and_rest, dict()),
    Action(rest.is_in_rest_multi, dict()),
    Action(rest.correct_url_in_rest_multi, dict()),
    Action(internal.same_value_of_key_in_all_sources, dict()),
    Action(internal.mandatory_keys_in_all_sources, dict()),
    Action(internal.all_keys_assigned_to_source, dict()),
    Action(internal.metadata_key_sources_do_not_contain_other_keys, dict()),
    Action(internal.thumbnail_key_sources_do_not_contain_other_keys, dict()),
    Action(internal.mandatory_keys_in_primary_db_schema_of_actor, dict()),
    Action(internal.other_keys_not_in_primary_db_schema_of_actor, dict()),
    Action(internal.mandatory_keys_in_all_sources_of_actor, dict()),
    Action(rest.is_complete_in_rest, dict()),
    Action(rest.mandatory_keys_in_rest, dict()),
]


IS_PUBLICATION_COMPLETE_AND_CONSISTENT = {
    process_client.LAYER_TYPE: IS_LAYER_COMPLETE_AND_CONSISTENT,
    process_client.MAP_TYPE: IS_MAP_COMPLETE_AND_CONSISTENT,
}
