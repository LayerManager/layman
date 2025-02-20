import copy

from owslib.feature.schema import get_schema as get_wfs_schema
import pytest

from layman import app, settings, names
from layman.layer import db
from layman.layer.geoserver import wfs as geoserver_wfs
from layman.layer.qgis import util as qgis_util, wms as qgis_wms
from layman.util import get_publication_info, get_publication_uuid
from test_tools.data import wfs as data_wfs
from test_tools import process_client, external_db
from tests import Publication, EnumTestTypes, PublicationValues
from tests.asserts.final.publication import util as assert_publ_util
from tests.dynamic_data import base_test, base_test_classes


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
            'external_table_uri': f"{external_db.URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE}&geo_column=wkb_geometry",
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
        'mandatory_cases': {},
        'ignore_cases': {},
    },
    'wfs20_update_points': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_2']],
        'data_method': data_wfs.get_wfs20_update_points_new_attr,
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]),
        },
    },
    'wfs20_update_points_with_attr_namespace': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_3']],
        'data_method': lambda *args: data_wfs.get_wfs20_update_points_new_attr(*args, with_attr_namespace=True),
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]),
        },
    },
    'wfs20_update_points_with_filter': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_4']],
        'data_method': lambda *args: data_wfs.get_wfs20_update_points_new_attr(*args, with_filter=True),
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]),
        },
    },
    'wfs20_replace_points': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_5']],
        'data_method': data_wfs.get_wfs20_replace_points_new_attr,
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]),
        },
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
        'mandatory_cases': {
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]),
        },
        'ignore_cases': {},
    },
    'wfs10_insert_points': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_7']],
        'data_method': data_wfs.get_wfs10_insert_points_new_attr,
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]),
        },
    },
    'wfs11_insert_points': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_8']],
        'data_method': data_wfs.get_wfs11_insert_points_new_attr,
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]),
        },
    },
    'wfs10_update_points_with_attr_namespace': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_9']],
        'data_method': lambda *args: data_wfs.get_wfs10_update_points_new(*args, with_attr_namespace=True),
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]),
        },
    },
    'wfs10_update_points_with_filter': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_10']],
        'data_method': lambda *args: data_wfs.get_wfs10_update_points_new(*args, with_filter=True),
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]),
        },
    },
    'wfs11_insert_polygon': {
        'simple': True,
        'attr_args_per_layer': [['new_attr_11']],
        'data_method': data_wfs.get_wfs11_insert_polygon_new_attr,
        'mandatory_cases': {},
        'ignore_cases': {
            frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]),
            frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]),
        },
    },
}

pytest_generate_tests = base_test.pytest_generate_tests


@pytest.mark.usefixtures('ensure_external_db', 'oauth2_provider_mock')
@pytest.mark.timeout(60)
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
                name=f"lr_{'_'.join(v.publ_name_part for v in parametrization.values_list)}",
            ),
            type=EnumTestTypes.OPTIONAL,
            specific_types={
                frozenset([StyleFileDomain.QML, LayerByTableLocation.EXTERNAL]): EnumTestTypes.IGNORE,
                **{
                    case: EnumTestTypes.IGNORE
                    for case in params['ignore_cases']
                },
                **{
                    case: EnumTestTypes.MANDATORY
                    for case in params['mandatory_cases']
                },
            },
            params=copy.deepcopy(params),
            specific_params=copy.deepcopy({
                # wfs20_complex_points fails for some UUIDs, see tests/dynamic_data/publications/issues/gs_wfst_update_replace.py
                frozenset([StyleFileDomain.SLD, LayerByTableLocation.INTERNAL, ]): {
                    'uuid': 'e6d24656-6d84-4015-89c9-b30d079af496',
                    'uuid2': '6e3647eb-cd63-4bc6-b21d-18a4161c6e68',
                },
                frozenset([StyleFileDomain.QML, LayerByTableLocation.INTERNAL, ]): {
                    'uuid': '5b6b83d4-714b-4f0e-ba50-225d9d2017f9',
                    'uuid2': 'd7247e9f-8f86-4438-82da-3f53e48df95f',
                },
                frozenset([StyleFileDomain.SLD, LayerByTableLocation.EXTERNAL, ]): {
                    'uuid': '0d8109ad-ef83-4a55-92c8-63d789755abd',
                    'uuid2': '377fff27-6c26-41d1-9d3d-1f96489b576f',
                },
            }, ),
            rest_args={
                'headers': AUTHN_HEADERS,
            }
        )
        for key, params in TEST_CASES.items()
    ]

    external_tables_to_create = [base_test_classes.ExternalTableDef(file_path=INPUT_FILE_PATH,
                                                                    db_schema=EXTERNAL_DB_SCHEMA,
                                                                    db_table=EXTERNAL_DB_TABLE,
                                                                    args={'launder': True},
                                                                    ),
                                 base_test_classes.ExternalTableDef(file_path=INPUT_FILE_PATH,
                                                                    db_schema=EXTERNAL_DB_SCHEMA,
                                                                    db_table=EXTERNAL_DB_TABLE_2,
                                                                    args={'launder': True},
                                                                    ),
                                 ]

    usernames_to_reserve = [WORKSPACE]

    def test_new_attribute(self, layer: Publication, rest_args, params, parametrization):
        workspace = self.workspace

        # ensure layers
        rest_args1 = {
            **rest_args,
            'uuid': params['uuid'],
        }
        self.ensure_publication(layer, args=rest_args1, scope='class')
        layer2 = Publication(name=f"{layer.name}_2", workspace=workspace, type=layer.type, uuid=params['uuid2'])
        rest_args2 = copy.deepcopy(rest_args) if 'external_table_uri' not in rest_args else {
            **rest_args,
            'external_table_uri': f"{external_db.URI_STR}?schema={EXTERNAL_DB_SCHEMA}&table={EXTERNAL_DB_TABLE_2}&geo_column=wkb_geometry",
        }
        self.ensure_publication(layer2, args=rest_args2, scope='class')

        # prepare data for WFS-T request and tuples of new attributes
        with app.app_context():
            wfst_data, new_attributes = self.prepare_wfst_data_and_new_attributes(layer, layer2, params)

        style_type = parametrization.style_file.style_type
        wfs_url = f"http://{settings.LAYMAN_SERVER_NAME}/geoserver/layman/wfs"
        table_uris = {}

        # get current attributes and assert that new attributes are not yet present
        old_db_attributes = {}
        old_wfs_properties = {}
        for layer_name, attr_names in new_attributes:
            # assert that all attr_names are not yet presented in DB table
            with app.app_context():
                table_uri = get_publication_info(workspace, process_client.LAYER_TYPE, layer_name,
                                                 context={'keys': ['table_uri']})['_table_uri']
            table_uris[layer_name] = table_uri
            old_db_attributes[layer_name] = db.get_all_table_column_names(table_uri.schema, table_uri.table,
                                                                          uri_str=table_uri.db_uri_str, )
            for attr_name in attr_names:
                assert attr_name not in old_db_attributes[layer_name], \
                    f"old_db_attributes={old_db_attributes[layer_name]}, attr_name={attr_name}"

            # assert that all attr_names are not yet presented in WFS feature type
            with app.app_context():
                layer_uuid = get_publication_uuid(workspace, self.publication_type, layer_name)
            gs_layer = names.get_layer_names_by_source(uuid=layer_uuid).wfs
            layer_schema = get_wfs_schema(wfs_url, typename=f"{gs_layer.workspace}:{gs_layer.name}",
                                          version=geoserver_wfs.VERSION, headers=AUTHN_HEADERS)
            old_wfs_properties[layer_name] = sorted(layer_schema['properties'].keys())

            if style_type == 'qml':
                # assert that all attr_names are not yet presented in QML
                with app.app_context():
                    assert qgis_wms.get_layer_info(workspace, layer_name)
                    old_qgis_attributes = qgis_util.get_layer_attribute_names(layer_uuid)
                assert all(attr_name not in old_qgis_attributes
                           for attr_name in attr_names), (attr_names, old_qgis_attributes)

        # make WFS-T request
        process_client.post_wfst(wfst_data, headers=AUTHN_HEADERS, workspace=names.GEOSERVER_WFS_WORKSPACE)
        for layer_name, _ in new_attributes:
            process_client.wait_for_publication_status(workspace, self.publication_type, layer_name,
                                                       headers=AUTHN_HEADERS)
            assert_publ_util.is_publication_valid_and_complete(layer)

        # assert that new attributes are present
        for layer_name, attr_names in new_attributes:
            # assert that exactly all attr_names were created in DB table
            with app.app_context():
                layer_uuid = get_publication_uuid(workspace, self.publication_type, layer_name)
            gs_layer = names.get_layer_names_by_source(uuid=layer_uuid).wfs
            table_uri = table_uris[layer_name]
            db_attributes = db.get_all_table_column_names(table_uri.schema, table_uri.table, uri_str=table_uri.db_uri_str)
            for attr_name in attr_names:
                assert attr_name in db_attributes, f"db_attributes={db_attributes}, attr_name={attr_name}"
            assert set(attr_names).union(set(old_db_attributes[layer_name])) == set(db_attributes)

            # assert that exactly all attr_names are present also in WFS feature type
            layer_schema = get_wfs_schema(wfs_url, typename=f"{gs_layer.workspace}:{gs_layer.name}",
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
                    new_qgis_attributes = qgis_util.get_layer_attribute_names(layer_uuid)
                assert all(attr_name in new_qgis_attributes for attr_name in attr_names), \
                    (attr_names, new_qgis_attributes)
            else:
                with app.app_context():
                    assert not qgis_wms.get_layer_info(workspace, layer_name)

    @staticmethod
    def prepare_wfst_data_and_new_attributes(layer, layer2, params):
        data_method = params['data_method']
        gs_layer = names.get_layer_names_by_source(uuid=get_publication_uuid(*layer)).wfs
        gs_layer2 = names.get_layer_names_by_source(uuid=get_publication_uuid(*layer2)).wfs
        if params['simple']:
            attr_args_per_layer = params['attr_args_per_layer']
            assert len(attr_args_per_layer) == 1
            attr_names = attr_args_per_layer[0]
            wfst_data = data_method(gs_layer.workspace, gs_layer.name, attr_names)
            new_attributes = [(layer.name, attr_names)]
        else:
            attr_args_per_layer = params['attr_args_per_layer']
            assert len(attr_args_per_layer) == 2
            wfst_data = data_method(
                geoserver_workspace=gs_layer.workspace,
                geoserver_layername1=gs_layer.name,
                geoserver_layername2=gs_layer2.name,
                **attr_args_per_layer[0],
                **attr_args_per_layer[1],
            )
            layer_attr_names = [attr for arg_attrs in attr_args_per_layer[0].values() for attr in arg_attrs]
            layer2_attr_names = [attr for arg_attrs in attr_args_per_layer[1].values() for attr in arg_attrs]
            new_attributes = [(layer.name, layer_attr_names), (layer2.name, layer2_attr_names)]
        return wfst_data, new_attributes
