import copy
import datetime
import os
import io
from lxml import etree as ET

from layman import settings, LaymanError
from layman.layer.filesystem import input_style


def get_layer_template_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), './layer-template.qml')


def get_project_template_path():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), './project-template.qgs')


def extent_to_xml_string(extent):
    return "\n".join([
        f"<{tag}>{extent}</{tag}>"
        for idx, tag in enumerate(['xmin', 'ymin', 'xmax', 'ymax'])
    ])


def get_layer_style_stream(workspace, layer):
    style_path = input_style.get_file_path(workspace, layer)
    if style_path and os.path.exists(style_path):
        with open(style_path, 'r') as style_file:
            style = style_file.read()
        style_stream = io.BytesIO(style.encode())
        return style_stream
    else:
        return None


def fill_layer_template(workspace, layer, uuid, native_bbox, qml_path):
    db_schema = workspace
    layer_name = layer
    wkb_type = 'MultiSurface'
    layer_type = 'MultiSurface'
    geometry_type = 'Polygon'
    db_table = layer

    template_path = get_layer_template_path()
    with open(template_path, 'r') as template_file:
        template_str = template_file.read()
    skeleton_xml_str = template_str.format(
        db_name=settings.LAYMAN_PG_DBNAME,
        db_host=settings.LAYMAN_PG_HOST,
        db_port=settings.LAYMAN_PG_PORT,
        db_user=settings.LAYMAN_PG_USER,
        db_password=settings.LAYMAN_PG_PASSWORD,
        layer_type=layer_type,
        db_schema=db_schema,
        db_table=db_table,
        layer_name=layer_name,
        layer_uuid=uuid,
        wkb_type=wkb_type,
        geometry_type=geometry_type,
        extent=extent_to_xml_string(native_bbox),
        default_action_canvas_value='{00000000-0000-0000-0000-000000000000}'
    )

    parser = ET.XMLParser(remove_blank_text=True)
    layer_xml = ET.fromstring(skeleton_xml_str.encode('utf-8'), parser=parser)
    qml_xml = ET.parse(qml_path, parser=parser)
    layer_el_tags = [el.tag for el in layer_xml.xpath('/maplayer/*')]
    tags_to_rewrite = ['legend', 'expressionfields']
    for qml_el in qml_xml.xpath('/qgis/*'):
        # print(f"qml_el={qml_el.tag}")
        tag = qml_el.tag
        if tag in layer_el_tags:
            if tag in tags_to_rewrite:
                layer_el = layer_xml.xpath(f'/maplayer/{tag}')[0]
                layer_el.getparent().replace(layer_el, copy.deepcopy(qml_el))
            else:
                raise LaymanError(47, data=f'Element {tag} already present in layer template.')
        else:
            layer_xml.append(copy.deepcopy(qml_el))

    full_xml_str = ET.tostring(layer_xml, encoding='unicode', pretty_print=True)
    return full_xml_str


def fill_project_template(workspace, layer, layer_uuid, layer_qml, epsg_codes, extent):
    wms_crs_list_values = "\n".join((f"<value>EPSG:{code}</value>" for code in epsg_codes))
    db_schema = workspace
    layer_name = layer
    layer_type = 'MultiSurface'
    db_table = layer
    creation_iso_datetime = datetime.datetime.utcnow().replace(microsecond=0).isoformat()

    template_path = get_project_template_path()
    with open(template_path, 'r') as template_file:
        template_str = template_file.read()
    return template_str.format(
        db_name=settings.LAYMAN_PG_DBNAME,
        db_host=settings.LAYMAN_PG_HOST,
        db_port=settings.LAYMAN_PG_PORT,
        db_user=settings.LAYMAN_PG_USER,
        db_password=settings.LAYMAN_PG_PASSWORD,
        layer_type=layer_type,
        db_schema=db_schema,
        db_table=db_table,
        layer_name=layer_name,
        layer_uuid=layer_uuid,
        layer_qml=layer_qml,
        wms_crs_list_values=wms_crs_list_values,
        creation_iso_datetime=creation_iso_datetime,
        extent=extent_to_xml_string(extent),
    )
