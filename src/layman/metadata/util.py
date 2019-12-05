from . import default_values
from xml.etree import ElementTree as ET

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


def get_default_values_dict():
    return {
        k: v for k, v in vars(default_values).items()
        if not k.startswith('_')
    }


def fill_template(template_path, filled_path=None):
    with open(template_path, 'r') as template_file:
        template_str = template_file.read()
    defaults = get_default_values_dict()
    xml_str = template_str.format(**defaults)
    root_el = ET.fromstring(xml_str)

    # for k, v in namespace_map.items():
    #     root_el.attrib[f"xmlns:{k}"] = v
    indent(root_el)
    el_tree = ET.ElementTree(root_el)

    if filled_path is not None:
        el_tree.write(
            filled_path,
            encoding='UTF-8',
            xml_declaration=True,
        )
