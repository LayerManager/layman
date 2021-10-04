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
                Action(publication.internal.correct_values_in_detail, {
                    'exp_publication_detail': {'name': 'basic_sld',
                                               'title': 'basic_sld',
                                               'type': 'layman.layer',
                                               'style_type': 'sld',
                                               'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196,
                                                                6269876.33561699],
                                               'access_rights': {'read': ['EVERYONE'], 'write': ['EVERYONE']},
                                               'file': {'path': 'layers/basic_sld/input_file/basic_sld.geojson', 'file_type': 'vector'},
                                               '_file': {
                                                   'path': '/layman_data_test/workspaces/dynamic_test_workspace/layers/basic_sld/input_file/basic_sld.geojson'},
                                               'db_table': {'name': 'basic_sld'},
                                               'description': None,
                                               'wfs': {'url': 'http://localhost:8000/geoserver/dynamic_test_workspace/wfs'},
                                               'wms': {'url': 'http://localhost:8000/geoserver/dynamic_test_workspace_wms/ows'},
                                               '_wms': {'url': 'http://geoserver:8080/geoserver/dynamic_test_workspace_wms/ows',
                                                        'workspace': 'dynamic_test_workspace_wms'},
                                               'style': {
                                                   'url': 'http://enjoychallenge.tech/rest/workspaces/dynamic_test_workspace/layers/basic_sld/style',
                                                   'type': 'sld'},
                                               'thumbnail': {
                                                   'url': 'http://enjoychallenge.tech/rest/workspaces/dynamic_test_workspace/layers/basic_sld/thumbnail',
                                                   'path': 'layers/basic_sld/thumbnail/basic_sld.png'},
                                               'metadata': {'csw_url': 'http://localhost:3080/csw',
                                                            'comparison_url': 'http://enjoychallenge.tech/rest/workspaces/dynamic_test_workspace/layers/basic_sld/metadata-comparison'}}
                }),
            ],
        },
    ],
}
