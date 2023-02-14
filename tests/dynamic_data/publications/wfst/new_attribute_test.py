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
        }, scope='class')
        self.import_external_table(INPUT_FILE_PATH, {
            'schema': EXTERNAL_DB_SCHEMA,
            'table': EXTERNAL_DB_TABLE_2,
        }, scope='class')

    def test_new_attribute(self, layer: Publication, rest_args, params, parametrization):
        # ensure layers
        if layer not in self.publications_to_cleanup_on_class_end:
            self.post_publication(layer, args=rest_args, scope='class')
        layer2 = Publication(name=f"{layer.name}_2", workspace=self.workspace, type=layer.type)
        rest_args2 = rest_args if 'db_connection' not in rest_args else {
            **rest_args,
            'db_connection': f"{external_db.URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE_2}&geo_column=wkb_geometry",
        }
        if layer2 not in self.publications_to_cleanup_on_class_end:
            self.post_publication(layer2, args=rest_args2, scope='class')

        # prepare data for WFS-T request and tuples of new attributes
        wfst_data, new_attributes = self.prepare_wfst_data_and_new_attributes(layer, layer2, params)

        # make WFS-T request and check that new attributes were added
        style_type = parametrization.style_file.style_type
        with app.app_context():
            table_uri = get_publication_info(self.workspace, layer.type, layer.name,
                                             context={'keys': ['table_uri']})['_table_uri']
        conn_cur = db_util.create_connection_cursor(table_uri.db_uri_str)
        self.post_wfst_and_check_attributes(self.workspace, new_attributes, wfst_data, style_type, conn_cur)

    @staticmethod
    def post_wfst_and_check_attributes(workspace, new_attributes, data_xml, style_type, conn_cur):
        with app.app_context():
            wfs_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/{workspace}/wfs"
            old_db_attributes = {}
            old_wfs_properties = {}
            for layer, attr_names in new_attributes:
                # test that all attr_names are not yet presented in DB table
                table_uri = get_publication_info(workspace, process_client.LAYER_TYPE, layer,
                                                 context={'keys': ['table_uri']})['_table_uri']
                old_db_attributes[layer] = db.get_all_table_column_names(table_uri.schema, table_uri.table,
                                                                         conn_cur=conn_cur)
                for attr_name in attr_names:
                    assert attr_name not in old_db_attributes[layer], \
                        f"old_db_attributes={old_db_attributes[layer]}, attr_name={attr_name}"
                layer_schema = get_wfs_schema(wfs_url, typename=f"{workspace}:{layer}",
                                              version=geoserver_wfs.VERSION, headers=AUTHN_HEADERS)
                old_wfs_properties[layer] = sorted(layer_schema['properties'].keys())
                if style_type == 'qml':
                    assert qgis_wms.get_layer_info(workspace, layer)
                    old_qgis_attributes = qgis_util.get_layer_attribute_names(workspace, layer)
                    assert all(attr_name not in old_qgis_attributes
                               for attr_name in attr_names), (attr_names, old_qgis_attributes)

            process_client.post_wfst(data_xml, headers=AUTHN_HEADERS, workspace=workspace)

            new_db_attributes = {}
            new_wfs_properties = {}
            for layer, attr_names in new_attributes:
                # test that exactly all attr_names were created in DB table
                table_uri = get_publication_info(workspace, process_client.LAYER_TYPE, layer,
                                                 context={'keys': ['table_uri']})['_table_uri']
                new_db_attributes[layer] = db.get_all_table_column_names(table_uri.schema, table_uri.table,
                                                                         conn_cur=conn_cur)
                for attr_name in attr_names:
                    assert attr_name in new_db_attributes[layer], \
                        f"new_db_attributes={new_db_attributes[layer]}, attr_name={attr_name}"
                assert set(attr_names).union(set(old_db_attributes[layer])) == set(new_db_attributes[layer])

                # test that exactly all attr_names were distinguished also in WFS feature type
                layer_schema = get_wfs_schema(wfs_url, typename=f"{workspace}:{layer}",
                                              version=geoserver_wfs.VERSION, headers=AUTHN_HEADERS)
                new_wfs_properties[layer] = sorted(layer_schema['properties'].keys())
                for attr_name in attr_names:
                    assert attr_name in new_wfs_properties[layer], \
                        f"new_wfs_properties={new_wfs_properties[layer]}, attr_name={attr_name}"
                assert set(attr_names).union(set(old_wfs_properties[layer])) == set(new_wfs_properties[layer]), \
                    set(new_wfs_properties[layer]).difference(set(attr_names).union(set(old_wfs_properties[layer])))
                if style_type == 'qml':
                    assert qgis_wms.get_layer_info(workspace, layer)
                    new_qgis_attributes = qgis_util.get_layer_attribute_names(workspace, layer)
                    assert all(attr_name in new_qgis_attributes
                               for attr_name in attr_names), (attr_names, new_qgis_attributes)
                else:
                    assert not qgis_wms.get_layer_info(workspace, layer)

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
