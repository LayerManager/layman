from xml.etree import ElementTree as ET
from io import BytesIO


NAMESPACES = {
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gmx': 'http://www.isotc211.org/2005/gmx',
    'xlink': 'http://www.w3.org/1999/xlink',
}
for k, v in NAMESPACES.items():
    ET.register_namespace(k, v)


def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def fill_template(template_path, template_values):
    with open(template_path, 'r') as template_file:
        template_str = template_file.read()
    xml_str = template_str.format(**template_values)
    root_el = ET.fromstring(xml_str)

    indent(root_el)
    el_tree = ET.ElementTree(root_el)

    file_object = BytesIO()

    el_tree.write(
        file_object,
        encoding='UTF-8',
        xml_declaration=True,
    )

    file_object.seek(0)

    return file_object
