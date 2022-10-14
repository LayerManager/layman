from layman import app
from layman.layer.micka import csw as csw_util
from test_tools import process_client, assert_util

METADATA_PROPERTIES = {
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
    # 'spatial_resolution',  # It is not updated for vector layer updated as raster one (https://trello.com/c/hRkFNuXP)
    'temporal_extent',
    'title',
    'wfs_url',
    'wms_url',
}


def expected_values_in_micka_metadata(workspace, publ_type, name, expected_values):
    assert publ_type == process_client.LAYER_TYPE
    with app.app_context():
        md_dict = csw_util.get_metadata_comparison(workspace, name)

    assert len(md_dict) == 1
    md_record = next(iter(md_record for md_record in md_dict.values()))

    assert_util.assert_same_values_for_keys(expected=expected_values,
                                            tested=md_record,
                                            )


def correct_values_in_layer_metadata(workspace, publ_type, name, http_method):
    assert publ_type == process_client.LAYER_TYPE
    with app.app_context():
        resp_json = process_client.get_workspace_layer_metadata_comparison(workspace, name,)
        assert METADATA_PROPERTIES.issubset(set(resp_json['metadata_properties'].keys()))
        for key, value in resp_json['metadata_properties'].items():
            assert value['equal_or_null'] is True, f'key={key}, value={value}'
            assert value['equal'] is True, f'key={key}, value={value}'

    with app.app_context():
        _, md_values = csw_util.get_template_path_and_values(workspace,
                                                             name,
                                                             http_method=http_method)
    exp_metadata = {key: value for key, value in md_values.items() if key in METADATA_PROPERTIES}
    exp_metadata['reference_system'] = [int(crs.split(':')[1]) for crs in exp_metadata['reference_system']]
    expected_values_in_micka_metadata(workspace, publ_type, name, exp_metadata)
