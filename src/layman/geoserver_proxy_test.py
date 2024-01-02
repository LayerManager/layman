import pytest

from layman import app
from test_tools.data import wfs as data_wfs
from . import geoserver_proxy


@pytest.mark.parametrize('wfst_data_method, hardcoded_attrs', [
    pytest.param(
        data_wfs.get_wfs20_insert_points_new_attr,
        ['wkb_geometry', 'name', 'labelrank'],
        id='insert',
    ),
    pytest.param(
        data_wfs.get_wfs20_replace_points_new_attr,
        ['wkb_geometry', 'name', 'labelrank'],
        id='replace',
    ),
    pytest.param(
        data_wfs.get_wfs20_update_points_new_attr,
        [],
        id='update',
    ),
])
def test_extract_attributes_and_layers_from_wfs_t(wfst_data_method, hardcoded_attrs):
    workspace = 'workspace_name'
    layer = 'layer_name'
    new_attrs = ['ok_attr', 'dangerous-attr-with-dashes']
    data_xml = wfst_data_method(workspace, layer, new_attrs)
    with app.app_context():
        extracted_attribs, extracted_layers = geoserver_proxy.extract_attributes_and_layers_from_wfs_t(data_xml)

    exp_attrs = {*new_attrs, *hardcoded_attrs}
    assert extracted_layers == {(workspace, layer)}
    assert extracted_attribs == {(workspace, layer, attr) for attr in exp_attrs}


@pytest.mark.parametrize('wfst_data_method, exp_attributes_and_layers', [
    pytest.param(
        data_wfs.get_wfs11_implicit_ns_update,
        ({('filip', 'poly', 'wkb_geometry')}, {('filip', 'poly')}),
        id='update_wfs1',
    ),
    pytest.param(
        data_wfs.get_wfs2_implicit_ns_update,
        ({('filip', 'poly', 'wkb_geometry')}, {('filip', 'poly')}),
        id='update_wfs2',
    ),
    pytest.param(
        data_wfs.get_wfs1_implicit_ns_delete,
        (set(), {('filip', 'europa_5514')}),
        id='delete_wfs1',
    ),
    pytest.param(
        data_wfs.get_wfs1_implicit_ns_insert,
        ({('filip', 'europa_5514', 'scalerank'), ('filip', 'europa_5514', 'featurecla'), ('filip', 'europa_5514', 'sovereignt'), ('filip', 'europa_5514', 'wkb_geometry'), ('filip', 'europa_5514', 'name'), ('filip', 'europa_5514', 'labelrank')}, {('filip', 'europa_5514')}),
        id='insert_wfs1',
    ),
])
def test_extract_attributes_and_layers_from_wfs_t_implicit_ws(wfst_data_method, exp_attributes_and_layers):
    binary_data = wfst_data_method()
    with app.app_context():
        attributes_and_layers = geoserver_proxy.extract_attributes_and_layers_from_wfs_t(binary_data)
    assert attributes_and_layers == exp_attributes_and_layers
