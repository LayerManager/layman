import copy
import datetime
import os
import io
from lxml import etree as ET

import crs as crs_def
from db import util as db_util
from layman import LaymanError
from layman.layer.filesystem import input_style
from layman.common import db as db_common
from . import wms

ELEMENTS_TO_REWRITE = ['legend', 'expressionfields']


def get_layer_template_path():
    file_name = './layer-template.qml'
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)


def get_project_template_path():
    file_name = './project-template.qgs'
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)


def get_style_template_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), './qml-template.qml')


def extent_to_xml_string(extent):
    return "\n".join([
        f"<{tag}>{extent[idx]}</{tag}>"
        for idx, tag in enumerate(['xmin', 'ymin', 'xmax', 'ymax'])
    ])


def get_original_style_path(workspace, layer):
    return input_style.get_file_path(workspace, layer)


def get_original_style_xml(workspace, layer):
    style_path = get_original_style_path(workspace, layer)
    parser = ET.XMLParser(remove_blank_text=True)
    qml_xml = ET.parse(style_path, parser=parser)
    return qml_xml


def get_layer_original_style_stream(workspace, layer):
    style_path = get_original_style_path(workspace, layer)
    if style_path and os.path.exists(style_path):
        with open(style_path, 'r') as style_file:
            style = style_file.read()
        style_stream = io.BytesIO(style.encode())
        result = style_stream
    else:
        result = None
    return result


def fill_layer_template(layer, uuid, native_bbox, crs, qml_xml, source_type, attrs_to_ensure, table_uri):
    db_schema = table_uri.schema
    table_name = table_uri.table
    geo_column = table_uri.geo_column
    layer_name = layer
    wkb_type = source_type
    qml_geometry = get_qml_geometry_from_qml(qml_xml)

    template_path = get_layer_template_path()
    with open(template_path, 'r') as template_file:
        template_str = template_file.read()
    skeleton_xml_str = template_str.format(
        db_name=table_uri.db_name,
        db_host=table_uri.hostname,
        db_port=table_uri.port,
        db_user=table_uri.username,
        db_password=table_uri.password,
        source_type=source_type,
        db_schema=db_schema,
        db_table=table_name,
        geo_column=geo_column,
        layer_name=layer_name,
        layer_uuid=uuid,
        wkb_type=wkb_type,
        qml_geometry=qml_geometry,
        extent=extent_to_xml_string(native_bbox),
        default_action_canvas_value='{00000000-0000-0000-0000-000000000000}',
        srid=db_util.get_srid(crs),
        qgis_template_spatialrefsys=crs_def.CRSDefinitions[crs].qgis_template_spatialrefsys,
    )

    launder_attribute_names(qml_xml)
    ensure_attributes_in_qml(qml_xml, attrs_to_ensure)

    parser = ET.XMLParser(remove_blank_text=True)
    layer_xml = ET.fromstring(skeleton_xml_str.encode('utf-8'), parser=parser)
    layer_el_tags = [el.tag for el in layer_xml.xpath('/maplayer/*')]
    for qml_el in qml_xml.xpath('/qgis/*'):
        # print(f"qml_el={qml_el.tag}")
        tag = qml_el.tag
        if tag in layer_el_tags:
            if tag in ELEMENTS_TO_REWRITE:
                layer_el = layer_xml.xpath(f'/maplayer/{tag}')[0]
                layer_el.getparent().replace(layer_el, copy.deepcopy(qml_el))
            else:
                raise LaymanError(47, data=f'Element {tag} already present in layer template.')
        else:
            layer_xml.append(copy.deepcopy(qml_el))
    skip_attrs = ['version']
    qml_root = qml_xml.getroot()
    for attr_name, attr_value in qml_root.attrib.items():
        if attr_name in skip_attrs:
            continue
        layer_xml.attrib[attr_name] = attr_value

    full_xml_str = ET.tostring(layer_xml, encoding='unicode', pretty_print=True)
    return full_xml_str


def fill_project_template(layer, layer_uuid, layer_qml, crs, epsg_codes, extent, source_type, table_uri):
    wms_crs_list_values = "\n".join((f"<value>{code}</value>" for code in epsg_codes))
    db_schema = table_uri.table
    table_name = table_uri.table
    geo_column = table_uri.geo_column
    layer_name = layer
    creation_iso_datetime = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    template_path = get_project_template_path()
    with open(template_path, 'r') as template_file:
        template_str = template_file.read()
    return template_str.format(
        db_name=table_uri.db_name,
        db_host=table_uri.hostname,
        db_port=table_uri.port,
        db_user=table_uri.username,
        db_password=table_uri.password,
        source_type=source_type,
        db_schema=db_schema,
        db_table=table_name,
        geo_column=geo_column,
        layer_name=layer_name,
        layer_uuid=layer_uuid,
        layer_qml=layer_qml,
        wms_crs_list_values=wms_crs_list_values,
        creation_iso_datetime=creation_iso_datetime,
        extent=extent_to_xml_string(extent),
        srid=db_util.get_srid(crs),
        qgis_template_spatialrefsys=crs_def.CRSDefinitions[crs].qgis_template_spatialrefsys,
    )


def get_layer_wms_crs_list_values(workspace, layer):
    file_path = wms.get_layer_file_path(workspace, layer)
    tree = ET.parse(file_path)
    crs_elements = tree.xpath("/qgis/properties/WMSCrsList")
    assert len(crs_elements) == 1
    crs_element = crs_elements[0]
    crs_list = {element.text for element in crs_element.iter("value")}
    return crs_list


def get_qml_geometry_from_qml(qml):
    symbol_to_geometry_type = {
        'marker': 'Point',
        'line': 'Line',
        'fill': 'Polygon',
    }
    symbol_types = {
        str(attr_value) for attr_value in qml.xpath('/qgis/renderer-v2/symbols/symbol/@type')
    }
    if not symbol_types:
        raise LaymanError(47, data=f'Symbol type not found in QML.')
    if len(symbol_types) > 1:
        raise LaymanError(47, data=f'Mixed symbol types in QML: {symbol_types}')
    symbol_type = next(iter(symbol_types))
    if symbol_type not in symbol_to_geometry_type:
        raise LaymanError(47, data=f'Unknown QGIS symbol type "{symbol_type}".')
    result = symbol_to_geometry_type[symbol_type]
    return result


def get_source_type(db_types, qml_geometry):
    result = None
    if qml_geometry == "Point":
        if "ST_MultiPoint" in db_types:
            result = "MultiPoint"
        elif "ST_Point" in db_types or not db_types:
            result = "Point"
    elif qml_geometry == "Line":
        if "ST_LineString" in db_types and "ST_MultiLineString" not in db_types:
            result = "LineString"
        elif "ST_LineString" in db_types and "ST_MultiLineString" in db_types:
            result = "MultiCurve"
        elif ("ST_LineString" not in db_types and "ST_MultiLineString" in db_types) or not db_types:
            result = "MultiLineString"
    elif qml_geometry == "Polygon":
        if "ST_Polygon" in db_types and "ST_MultiPolygon" not in db_types:
            result = "Polygon"
        elif "ST_Polygon" in db_types and "ST_MultiPolygon" in db_types:
            result = "MultiSurface"
        elif ("ST_Polygon" not in db_types and "ST_MultiPolygon" in db_types) or not db_types:
            result = "MultiPolygon"
    elif qml_geometry == "Unknown geometry":
        if "ST_GeometryCollection" in db_types:
            result = "GeometryCollection"
    if result is None:
        raise LaymanError(47,
                          data=f'Unknown combination of QML geometry "{qml_geometry}" and DB geometry types '
                               f'{db_types}')
    return result


FIELD_XML_ATTRIBUTES = [
    ("/qgis/renderer-v2", "attr"),
    ("/qgis/fieldConfiguration/field", "name"),
    ("/qgis/aliases/alias", "field"),
    ("/qgis/defaults/default", "field"),
    ("/qgis/constraints/constraint", "field"),
    ("/qgis/constraintExpressions/constraint", "field"),
    ("/qgis/attributetableconfig/columns/column[@type='field']", "name"),
    ("/qgis/editable/field", "name"),
    ("/qgis/labelOnTop/field", "name"),
]


def launder_attribute_names(qml):
    for el_path, attr_name in FIELD_XML_ATTRIBUTES:
        for element in qml.xpath(f'{el_path}[@{attr_name}]'):
            element.attrib[attr_name] = db_common.launder_attribute_name(element.attrib[attr_name])


def get_attribute_names_from_qml(qml):
    result = set()
    for el_path, attr_name in FIELD_XML_ATTRIBUTES:
        for element in qml.xpath(f'{el_path}[@{attr_name}]'):
            result.add(element.attrib[attr_name])
    return result


def ensure_attributes_in_qml(qml, attrs_to_ensure):
    existing_attr_names = get_attribute_names_from_qml(qml)
    missing_attrs = [attr for attr in attrs_to_ensure if attr.name not in existing_attr_names]

    parser = ET.XMLParser(remove_blank_text=True)
    field_template = """
        <field configurationFlags="None" name="{field_name}">
          <editWidget type="TextEdit">
            <config>
              <Option/>
            </config>
          </editWidget>
        </field>
    """

    fields_el = qml.xpath(f'/qgis/fieldConfiguration')[0]
    for attr in missing_attrs:
        if attr.data_type != 'character varying':
            raise LaymanError(47, data=f'Attribute "{attr.name}" can not be automatically added to QML, because of its '
                                       f'unsupported data type "{attr.data_type}". This is probably caused by '
                                       f'inconsistency between attributes used in QML style and attributes in data '
                                       f'file. You can fix this by uploading QML style listing all data attributes.')
        field_el = ET.fromstring(field_template.format(field_name=attr.name), parser=parser)
        fields_el.append(field_el)


def get_attribute_names_from_qgs(qgs):
    result = set()
    for element in qgs.xpath(f'/qgis/projectlayers/maplayer/fieldConfiguration/field'):
        result.add(element.attrib['name'])
    return result


def get_layer_attribute_names(workspace, layer):
    qgs_path = wms.get_layer_file_path(workspace, layer)
    parser = ET.XMLParser(remove_blank_text=True)
    qgs_xml = ET.parse(qgs_path, parser=parser)
    return get_attribute_names_from_qgs(qgs_xml)


def get_current_style_xml(style_template_file, layer_template_file, layer_project_file, original_qml_path):
    parser = ET.XMLParser(remove_blank_text=True)

    qml_xml_tree = ET.parse(style_template_file, parser=parser)
    qml_xml = qml_xml_tree.getroot()

    qgs_xml = ET.parse(layer_project_file, parser=parser)
    qgs_maplayers = qgs_xml.xpath('/qgis/projectlayers/maplayer')
    assert len(qgs_maplayers) == 1
    qgs_maplayer = qgs_maplayers[0]

    layer_template_xml = ET.parse(layer_template_file, parser=parser)
    layer_template_maplayers = layer_template_xml.xpath('/maplayer')
    assert len(layer_template_maplayers) == 1
    elements_not_copy = [el.tag for el in layer_template_maplayers[0].xpath('/maplayer/*')
                         if el.tag not in ELEMENTS_TO_REWRITE]

    original_qml = ET.parse(original_qml_path, parser=parser).getroot()
    for name, value in original_qml.attrib.items():
        qml_xml.attrib[name] = value

    for element in qgs_maplayer:
        if element.tag not in elements_not_copy:
            qml_xml.append(copy.deepcopy(element))

    full_xml_str = ET.tostring(qml_xml, encoding='unicode', pretty_print=True)
    return full_xml_str
