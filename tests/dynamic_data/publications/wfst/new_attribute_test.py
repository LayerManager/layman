import copy

from owslib.feature.schema import get_schema as get_wfs_schema
import pytest

from db import util as db_util
from layman import app, settings
from layman.layer import db
from layman.layer.geoserver import wfs as geoserver_wfs
from layman.layer.qgis import util as qgis_util, wms as qgis_wms
from layman.util import get_publication_info
from test_tools.data import wfs as data_wfs
from test_tools import process_client, external_db
from tests import Publication, EnumTestTypes, PublicationValues
from tests.dynamic_data import base_test


INPUT_FILE_PATH = 'tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'
EXTERNAL_DB_TABLE = 'ne_110m_admin_0_countries'
EXTERNAL_DB_TABLE_2 = 'ne_110m_admin_0_countries_2'
EXTERNAL_DB_SCHEMA = 'public'


class StyleFileDomain(base_test.StyleFileDomainBase):
    SLD = ((None, 'sld'), 'sld')
    QML = (('sample/style/ne_10m_admin_0_countries.qml', 'qml'), 'qml')


class LayerByTableLocation(base_test.PublicationByDefinitionBase):
    INTERNAL = (PublicationValues(
        type=process_client.LAYER_TYPE,
        definition={
            'file_paths': [INPUT_FILE_PATH],
        },
        info_values={},
        thumbnail='',
        legend_image='',
    ), 'internal_table')
    EXTERNAL = (PublicationValues(
        type=process_client.LAYER_TYPE,
        definition={
            'db_connection': f"{external_db.URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE}&geo_column=wkb_geometry",
        },
        info_values={},
        thumbnail='',
        legend_image='',
    ), 'external_table')


# It seems GeoServer is somehow sensitive to workspace and layer names, maybe to their length,
# when receiving WFS-T requests, specifically wfs20_complex_points.
# In this test case, GeoServer returns 500 for some combination of names.
WORKSPACE = 'test_wfst_attr'
AUTHN_HEADERS = process_client.get_authz_headers(WORKSPACE)

TEST_CASES = {
    'wfs20_insert_points_two_attributes': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_1a', 'new_attr_1b']],
        'data_method': data_wfs.get_wfs20_insert_points_new_attr,
    },
    'wfs20_update_points': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_2']],
        'data_method': data_wfs.get_wfs20_update_points_new_attr,
    },
    'wfs20_update_points_with_attr_namespace': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_3']],
        'data_method': lambda *args: data_wfs.get_wfs20_update_points_new_attr(*args, with_attr_namespace=True),
    },
    'wfs20_update_points_with_filter': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_4']],
        'data_method': lambda *args: data_wfs.get_wfs20_update_points_new_attr(*args, with_filter=True),
    },
    'wfs20_replace_points': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_5']],
        'data_method': data_wfs.get_wfs20_replace_points_new_attr,
    },
    'wfs20_complex_points': {
        'simple': False,
        'attr_args_per_layer': [{
            'attr_names_insert1': ['new_layer1_attr_insert'],
            'attr_names_replace': ['new_layer1_attr_replace'],
        }, {
            'attr_names_insert2': ['new_layer2_attr_insert'],
            'attr_names_update': ['new_layer2_attr_update'],
        }],
        'data_method': data_wfs.get_wfs20_complex_new_attr,
    },
    'wfs10_insert_points': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_7']],
        'data_method': data_wfs.get_wfs10_insert_points_new_attr,
    },
    'wfs11_insert_points': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_8']],
        'data_method': data_wfs.get_wfs11_insert_points_new_attr,
    },
    'wfs10_update_points_with_attr_namespace': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_9']],
        'data_method': lambda *args: data_wfs.get_wfs10_update_points_new(*args, with_attr_namespace=True),
    },
    'wfs10_update_points_with_filter': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_10']],
        'data_method': lambda *args: data_wfs.get_wfs10_update_points_new(*args, with_filter=True),
    },
    'wfs11_insert_polygon': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_11']],
        'data_method': data_wfs.get_wfs11_insert_polygon_new_attr,
    },
}

pytest_generate_tests = base_test.pytest_generate_tests


@pytest.mark.usefixtures('ensure_external_db', 'liferay_mock')
class TestNewAttribute(base_test.TestSingleRestPublication):
    workspace = WORKSPACE

    publication_type = process_client.LAYER_TYPE

    rest_parametrization = [
        StyleFileDomain,
        LayerByTableLocation,
    ]

    test_cases = [
        base_test.TestCaseType(
            key=key,
            publication=lambda cls, parametrization: Publication(
                workspace=cls.workspace,
                type=cls.publication_type,
                name=f"lr_{'_'.join(v.publ_name_part for v in parametrization.values_list)}"),
            type=EnumTestTypes.MANDATORY,
            specific_types={frozenset([StyleFileDomain.QML, LayerByTableLocation.EXTERNAL]): EnumTestTypes.IGNORE},
            params=copy.deepcopy(params),
            rest_args={
                'headers': AUTHN_HEADERS,
            }
        )
        for key, params in TEST_CASES.items()
    ]

    def before_class(self):
        process_client.ensure_reserved_username(self.workspace, headers=AUTHN_HEADERS)
        self.import_external_table(INPUT_FILE_PATH, {
            'schema': EXTERNAL_DB_SCHEMA,
            'table': EXTERNAL_DB_TABLE,
            'launder': True,
        }, scope='class')
        self.import_external_table(INPUT_FILE_PATH, {
            'schema': EXTERNAL_DB_SCHEMA,
            'table': EXTERNAL_DB_TABLE_2,
            'launder': True,
        }, scope='class')

    def test_new_attribute(self, layer: Publication, rest_args, params, parametrization):
        workspace = self.workspace

        # ensure layers
        self.ensure_publication(layer, args=rest_args, scope='class')
        layer2 = Publication(name=f"{layer.name}_2", workspace=workspace, type=layer.type)
        rest_args2 = rest_args if 'db_connection' not in rest_args else {
            **rest_args,
            'db_connection': f"{external_db.URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE_2}&geo_column=wkb_geometry",
        }
        self.ensure_publication(layer2, args=rest_args2, scope='class')

        # prepare data for WFS-T request and tuples of new attributes
        wfst_data, new_attributes = self.prepare_wfst_data_and_new_attributes(layer, layer2, params)

        style_type = parametrization.style_file.style_type
        wfs_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{workspace}/wfs"
        table_uris = {}
        conn_cur = None

        # get current attributes and assert that new attributes are not yet present
        old_db_attributes = {}
        old_wfs_properties = {}
        for layer_name, attr_names in new_attributes:
            # assert that all attr_names are not yet presented in DB table
            with app.app_context():
                table_uri = get_publication_info(workspace, process_client.LAYER_TYPE, layer_name,
                                                 context={'keys': ['table_uri']})['_table_uri']
            conn_cur = conn_cur or db_util.create_connection_cursor(table_uri.db_uri_str)
            table_uris[layer_name] = table_uri
            old_db_attributes[layer_name] = db.get_all_table_column_names(table_uri.schema, table_uri.table,
                                                                          conn_cur=conn_cur)
            for attr_name in attr_names:
                assert attr_name not in old_db_attributes[layer_name], \
                    f"old_db_attributes={old_db_attributes[layer_name]}, attr_name={attr_name}"

            # assert that all attr_names are not yet presented in WFS feature type
            layer_schema = get_wfs_schema(wfs_url, typename=f"{workspace}:{layer_name}",
                                          version=geoserver_wfs.VERSION, headers=AUTHN_HEADERS)
            old_wfs_properties[layer_name] = sorted(layer_schema['properties'].keys())

            if style_type == 'qml':
                # assert that all attr_names are not yet presented in QML
                with app.app_context():
                    assert qgis_wms.get_layer_info(workspace, layer_name)
                    old_qgis_attributes = qgis_util.get_layer_attribute_names(workspace, layer_name)
                assert all(attr_name not in old_qgis_attributes
                           for attr_name in attr_names), (attr_names, old_qgis_attributes)

        # make WFS-T request
        process_client.post_wfst(wfst_data, headers=AUTHN_HEADERS, workspace=workspace)

        # assert that new attributes are present
        for layer_name, attr_names in new_attributes:
            # assert that exactly all attr_names were created in DB table
            table_uri = table_uris[layer_name]
            db_attributes = db.get_all_table_column_names(table_uri.schema, table_uri.table, conn_cur=conn_cur)
            for attr_name in attr_names:
                assert attr_name in db_attributes, f"db_attributes={db_attributes}, attr_name={attr_name}"
            assert set(attr_names).union(set(old_db_attributes[layer_name])) == set(db_attributes)

            # assert that exactly all attr_names are present also in WFS feature type
            layer_schema = get_wfs_schema(wfs_url, typename=f"{workspace}:{layer_name}",
                                          version=geoserver_wfs.VERSION, headers=AUTHN_HEADERS)
            wfs_properties = sorted(layer_schema['properties'].keys())
            for attr_name in attr_names:
                assert attr_name in wfs_properties, f"wfs_properties={wfs_properties}, attr_name={attr_name}"
            assert set(attr_names).union(set(old_wfs_properties[layer_name])) == set(wfs_properties), \
                set(wfs_properties).difference(set(attr_names).union(set(old_wfs_properties[layer_name])))

            if style_type == 'qml':
                # assert that exactly all attr_names are present also in QML
                with app.app_context():
                    assert qgis_wms.get_layer_info(workspace, layer_name)
                    new_qgis_attributes = qgis_util.get_layer_attribute_names(workspace, layer_name)
                assert all(attr_name in new_qgis_attributes for attr_name in attr_names), \
                    (attr_names, new_qgis_attributes)
            else:
                with app.app_context():
                    assert not qgis_wms.get_layer_info(workspace, layer_name)

    @staticmethod
    def prepare_wfst_data_and_new_attributes(layer, layer2, params):
        data_method = params['data_method']
        if params['simple']:
            attr_args_per_layer = params['attr_args_per_layer']
            assert len(attr_args_per_layer) == 1
            attr_names = attr_args_per_layer[0]
            wfst_data = data_method(layer.workspace, layer.name, attr_names)
            new_attributes = [(layer.name, attr_names)]
        else:
            attr_args_per_layer = params['attr_args_per_layer']
            assert len(attr_args_per_layer) == 2
            wfst_data = data_method(
                workspace=layer.workspace,
                layername1=layer.name,
                layername2=layer2.name,
                **attr_args_per_layer[0],
                **attr_args_per_layer[1],
            )
            layer_attr_names = [attr for arg_attrs in attr_args_per_layer[0].values() for attr in arg_attrs]
            layer2_attr_names = [attr for arg_attrs in attr_args_per_layer[1].values() for attr in arg_attrs]
            new_attributes = [(layer.name, layer_attr_names), (layer2.name, layer2_attr_names)]
        return wfst_data, new_attributes
