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
@pytest.mark.parametrize('gs_workspace, gs_layername, exp_layername', [
    pytest.param(
        'layman',
        'l_ae82a4d1-c915-46bb-89d5-4e3818b6df3f',
        'ae82a4d1-c915-46bb-89d5-4e3818b6df3f',
        id='layman-layer'
    ),
    pytest.param(
        'layman_wms',
        'l_ae82a4d1-c915-46bb-89d5-4e3818b6df3f',
        'ae82a4d1-c915-46bb-89d5-4e3818b6df3f',
        id='layman_wms-layer'
    ),
    pytest.param(
        'other_workspace',
        'l_ae82a4d1-c915-46bb-89d5-4e3818b6df3f',
        None,
        id='wrong_ws'
    ),
    pytest.param(
        'layman',
        'ae82a4d1-c915-46bb-89d5-4e3818b6df3f',
        None,
        id='layman-uuid'
    ),
    pytest.param(
        'layman',
        'layer_name',
        None,
        id='layman-layer_name'
    ),
])
def test_extract_attributes_and_layers_from_wfs_t(wfst_data_method, hardcoded_attrs, gs_workspace, gs_layername, exp_layername):
    new_attrs = ['ok_attr', 'dangerous-attr-with-dashes']
    data_xml = wfst_data_method(gs_workspace, gs_layername, new_attrs)
    with app.app_context():
        extracted_attribs, extracted_layers = geoserver_proxy.extract_attributes_and_layers_from_wfs_t(data_xml)

    exp_attrs = {*new_attrs, *hardcoded_attrs} if exp_layername is not None else set()
    exp_layers = {exp_layername} if exp_layername is not None else set()
    assert extracted_layers == exp_layers
    assert extracted_attribs == {(exp_layername, attr) for attr in exp_attrs}


@pytest.mark.parametrize('wfst_data_method, exp_attributes_and_layers', [
    pytest.param(
        data_wfs.get_wfs11_implicit_ns_update,
        ({('0795d7ba-adf9-4b8b-8438-32d8b2410d54', 'wkb_geometry')}, {('0795d7ba-adf9-4b8b-8438-32d8b2410d54')}),
        id='update_wfs1',
    ),
    pytest.param(
        data_wfs.get_wfs2_implicit_ns_update,
        ({('0795d7ba-adf9-4b8b-8438-32d8b2410d54', 'wkb_geometry')}, {('0795d7ba-adf9-4b8b-8438-32d8b2410d54')}),
        id='update_wfs2',
    ),
    pytest.param(
        data_wfs.get_wfs1_implicit_ns_delete,
        (set(), {('2c08994e-5014-463a-bfb2-46f980c9fc97')}),
        id='delete_wfs1',
    ),
    pytest.param(
        data_wfs.get_wfs1_implicit_ns_insert,
        ({('2c08994e-5014-463a-bfb2-46f980c9fc97', 'scalerank'), ('2c08994e-5014-463a-bfb2-46f980c9fc97', 'featurecla'), ('2c08994e-5014-463a-bfb2-46f980c9fc97', 'sovereignt'), ('2c08994e-5014-463a-bfb2-46f980c9fc97', 'wkb_geometry'), ('2c08994e-5014-463a-bfb2-46f980c9fc97', 'name'), ('2c08994e-5014-463a-bfb2-46f980c9fc97', 'labelrank')}, {('2c08994e-5014-463a-bfb2-46f980c9fc97')}),
        id='insert_wfs1',
    ),
])
def test_extract_attributes_and_layers_from_wfs_t_implicit_ws(wfst_data_method, exp_attributes_and_layers):
    binary_data = wfst_data_method()
    with app.app_context():
        attributes_and_layers = geoserver_proxy.extract_attributes_and_layers_from_wfs_t(binary_data)
    assert attributes_and_layers == exp_attributes_and_layers
