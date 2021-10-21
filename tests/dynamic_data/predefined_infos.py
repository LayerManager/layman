LAYER = {
    'access_rights': {'read': ['EVERYONE'], 'write': ['EVERYONE']},
    'description': None,
    'metadata': {'csw_url': 'http://localhost:3080/csw', }
}


SLD_LAYER = {
    **LAYER,
    'style_type': 'sld',
    'style': {'type': 'sld'},
}


SLD_VECTOR_LAYER = {
    **SLD_LAYER,
    'wfs': {'url': 'http://localhost:8000/geoserver/dynamic_test_workspace/wfs'},
    'file': {'file_type': 'vector'},
}


SLD_RASTER_LAYER = {
    **SLD_LAYER,
    'file': {'file_type': 'raster'},
}


BASIC_SLD_LAYER = {
    **SLD_VECTOR_LAYER,
    'db_table': {'name': 'basic_sld'},
    'bounding_box': [1571204.369948366, 6268896.225570714, 1572590.854206196, 6269876.33561699],
    'file': {'path': 'layers/basic_sld/input_file/basic_sld.geojson', 'file_type': 'vector'},
    '_file': {
        'path': '/layman_data_test/workspaces/dynamic_test_workspace/layers/basic_sld/input_file/basic_sld.geojson'},
}
