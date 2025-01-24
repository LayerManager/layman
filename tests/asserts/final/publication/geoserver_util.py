from layman import app, util as layman_util, names
from . import process_client


def is_complete_in_workspace_wms_instance(wms_instance, name, *, validate_metadata_url):
    assert wms_instance.contents
    assert name in wms_instance.contents, "Layer not found in Capabilities."
    wms_layer = wms_instance.contents[name]
    for style_name, style_values in wms_layer.styles.items():
        assert 'legend' in style_values, f'style_name={style_name}, style_values={style_values}'
    if validate_metadata_url:
        assert len(wms_layer.metadataUrls) == 1
        assert wms_layer.metadataUrls[0]['url'].startswith('http://localhost:3080/record/xml/m-')


def get_wms_layername(workspace, name):
    with app.app_context():
        uuid = layman_util.get_publication_uuid(workspace, process_client.LAYER_TYPE, name)
    return names.get_layer_names_by_source(uuid=uuid, )['wms']
