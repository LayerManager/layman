def is_complete_in_workspace_wms_instance(wms_instance, name):
    assert wms_instance.contents
    assert name in wms_instance.contents
    wms_layer = wms_instance.contents[name]
    for style_name, style_values in wms_layer.styles.items():
        assert 'legend' in style_values, f'style_name={style_name}, style_values={style_values}'
