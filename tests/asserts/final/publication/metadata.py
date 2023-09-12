from layman import app, settings
from layman.layer.micka import csw as layer_csw_util
from layman.map.micka import csw as map_csw_util
from test_tools import process_client, assert_util

LAYER_METADATA_PROPERTIES = {
    'abstract',
    'extent',
    'graphic_url',
    'identifier',
    'layer_endpoint',
    'language',
    'organisation_name',
    'publication_date',
    'reference_system',
    'revision_date',
    # 'spatial_resolution',  # It is not updated for vector layer updated as raster one (probably because of bug in Micka)
    'temporal_extent',
    'title',
    'wfs_url',
    'wms_url',
}

MAP_METADATA_PROPERTIES = {
    'abstract',
    'extent',
    'graphic_url',
    'identifier',
    'map_endpoint',
    'map_file_endpoint',
    'operates_on',
    'organisation_name',
    'publication_date',
    'reference_system',
    'revision_date',
    'title',
}


def expected_values_in_micka_metadata(workspace, publ_type, name, expected_values):
    md_comparison_method = {
        process_client.LAYER_TYPE: layer_csw_util.get_metadata_comparison,
        process_client.MAP_TYPE: map_csw_util.get_metadata_comparison,
    }[publ_type]
    with app.app_context():
        md_dict = md_comparison_method(workspace, name)

    assert len(md_dict) == 1
    md_record = next(iter(md_record for md_record in md_dict.values()))

    assert_util.assert_same_values_for_keys(expected=expected_values,
                                            tested=md_record,
                                            )


def correct_values_in_metadata(workspace, publ_type, name, http_method, *, exp_values=None, actor_name=None):
    exp_values = exp_values or {}
    actor_name = actor_name or settings.ANONYM_USER
    md_props = {
        process_client.LAYER_TYPE: LAYER_METADATA_PROPERTIES,
        process_client.MAP_TYPE: MAP_METADATA_PROPERTIES,
    }[publ_type]
    with app.app_context():
        resp_json = process_client.get_workspace_publication_metadata_comparison(publ_type, workspace, name,
                                                                                 actor_name=actor_name)
        assert md_props.issubset(set(resp_json['metadata_properties'].keys()))
        for key, value in resp_json['metadata_properties'].items():
            assert value['equal_or_null'] is True, f'key={key}, value={value}'
            assert value['equal'] is True, f'key={key}, value={value}'

    get_template_path_and_values_method, args = {
        process_client.LAYER_TYPE: (layer_csw_util.get_template_path_and_values, {}),
        process_client.MAP_TYPE: (map_csw_util.get_template_path_and_values, {'actor_name': actor_name}),
    }[publ_type]
    with app.app_context():
        _, md_values = get_template_path_and_values_method(workspace, name, http_method=http_method, **args)
    exp_metadata = {key: value for key, value in md_values.items() if key in md_props}
    if publ_type == process_client.LAYER_TYPE:
        exp_metadata['reference_system'] = [int(crs.split(':')[1]) for crs in exp_metadata['reference_system']]
    for key, value in exp_values.items():
        assert exp_metadata[key] == value, f"Template value differ from expected value, key={key}"
    expected_values_in_micka_metadata(workspace, publ_type, name, exp_metadata)
