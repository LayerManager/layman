from tests import Action
from test_tools import process_client
from . import geoserver, geoserver_proxy, internal, internal_rest, rest, metadata


IS_LAYER_COMPLETE_AND_CONSISTENT = [
    Action(internal.source_has_its_key_or_it_is_empty, {}),
    Action(internal.source_internal_keys_are_subset_of_source_sibling_keys, {}),
    Action(internal_rest.same_title_in_source_and_rest_multi, {}),
    Action(internal_rest.same_values_in_internal_and_rest, {}),
    Action(rest.is_in_rest_multi, {}),
    Action(rest.correct_url_in_rest_multi, {}),
    Action(internal.same_value_of_key_in_all_sources, {}),
    Action(internal.mandatory_keys_in_all_sources, {}),
    Action(internal.all_keys_assigned_to_source, {}),
    Action(internal.metadata_key_sources_do_not_contain_other_keys, {}),
    Action(internal.thumbnail_key_sources_do_not_contain_other_keys, {}),
    Action(internal.mandatory_keys_in_primary_db_schema_of_actor, {}),
    Action(internal.other_keys_not_in_primary_db_schema_of_actor, {}),
    Action(internal.mandatory_keys_in_all_sources_of_actor, {}),
    Action(internal.nodata_preserved_in_normalized_raster, {}),
    Action(internal.size_and_position_preserved_in_normalized_raster, {}),
    Action(internal.stats_preserved_in_normalized_raster, {}),
    Action(internal.wfs_wms_status_available, {}),
    Action(rest.is_complete_in_rest, {}),
    Action(rest.mandatory_keys_in_rest, {}),
    Action(geoserver.is_complete_in_internal_workspace_wms, {}),
    Action(geoserver_proxy.is_complete_in_workspace_wms_1_3_0, {}),
    Action(geoserver_proxy.workspace_wfs_2_0_0_capabilities_available_if_vector, {}),
]

IS_MAP_COMPLETE_AND_CONSISTENT = [
    Action(internal.source_has_its_key_or_it_is_empty, {}),
    Action(internal.source_internal_keys_are_subset_of_source_sibling_keys, {}),
    Action(internal_rest.same_title_in_source_and_rest_multi, {}),
    Action(internal_rest.same_values_in_internal_and_rest, {}),
    Action(rest.is_in_rest_multi, {}),
    Action(rest.correct_url_in_rest_multi, {}),
    Action(internal.same_value_of_key_in_all_sources, {}),
    Action(internal.mandatory_keys_in_all_sources, {}),
    Action(internal.all_keys_assigned_to_source, {}),
    Action(internal.metadata_key_sources_do_not_contain_other_keys, {}),
    Action(internal.thumbnail_key_sources_do_not_contain_other_keys, {}),
    Action(internal.mandatory_keys_in_primary_db_schema_of_actor, {}),
    Action(internal.other_keys_not_in_primary_db_schema_of_actor, {}),
    Action(internal.mandatory_keys_in_all_sources_of_actor, {}),
    Action(rest.is_complete_in_rest, {}),
    Action(rest.mandatory_keys_in_rest, {}),
]


IS_PUBLICATION_COMPLETE_AND_CONSISTENT = {
    process_client.LAYER_TYPE: IS_LAYER_COMPLETE_AND_CONSISTENT,
    process_client.MAP_TYPE: IS_MAP_COMPLETE_AND_CONSISTENT,
}
