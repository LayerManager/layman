import os
from xml.etree import ElementTree as ET
from io import BytesIO
from owslib.csw import CatalogueServiceWeb
from owslib.util import nspath_eval
from flask import g, current_app
from layman import settings, LaymanError
import requests


NAMESPACES = {
    'csw': 'http://www.opengis.net/cat/csw/2.0.2',
    'ows': 'http://www.opengis.net/ows/1.1',
    'dc': 'http://purl.org/dc/elements/1.1/',
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
    file_object = fill_template_as_pretty_file_object(template_path, template_values)
    return file_object


def fill_template_as_str(template_path, template_values):
    with open(template_path, 'r') as template_file:
        template_str = template_file.read()
    xml_str = template_str.format(**template_values)
    return xml_str


def fill_template_as_pretty_el(template_path, template_values):
    xml_str = fill_template_as_str(template_path, template_values)
    root_el = ET.fromstring(xml_str)

    indent(root_el)
    return root_el


def fill_template_as_pretty_file_object(template_path, template_values):
    root_el = fill_template_as_pretty_el(template_path, template_values)
    el_tree = ET.ElementTree(root_el)
    file_object = BytesIO()
    el_tree.write(
        file_object,
        encoding='UTF-8',
        xml_declaration=True,
    )
    file_object.seek(0)
    return file_object


def fill_template_as_pretty_str(template_path, template_values):
    root_el = fill_template_as_pretty_el(template_path, template_values)
    pretty_str = ET.tostring(root_el, encoding='unicode')
    return pretty_str


def create_csw():
    opts = {} if settings.CSW_BASIC_AUTHN is None else {
        'username': settings.CSW_BASIC_AUTHN[0],
        'password': settings.CSW_BASIC_AUTHN[1],
    }
    csw = CatalogueServiceWeb(settings.CSW_URL, **opts) if settings.CSW_URL is not None else None
    return csw


def csw_insert(template_values):
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'csw-insert-template.xml')
    xml_str = fill_template_as_str(template_path, template_values)
    # print(f"xml_str=\n{xml_str}")
    r = requests.post(settings.CSW_URL, auth=settings.CSW_BASIC_AUTHN, data=xml_str.encode('utf-8'))
    r.raise_for_status()
    root_el = ET.fromstring(r.content)

    def is_record_exists_exception(root_el):
        return len(root_el) != 1 or \
                len(root_el) != 1 or \
                root_el[0].tag != nspath_eval('ows:Exception', NAMESPACES) or \
                "exceptionCode" not in root_el[0].attrib or \
                root_el[0].attrib["exceptionCode"] != 'TransactionFailed' or \
                len(root_el[0]) != 1 or \
                root_el[0][0].tag != nspath_eval('ows:ExceptionText', NAMESPACES) or \
                not root_el[0][0].text.startswith('Record exists')

    if root_el.tag == nspath_eval('ows:ExceptionReport', NAMESPACES):
        if is_record_exists_exception(root_el):
            raise LaymanError(36, data={
                'exception_code': root_el[0].attrib["exceptionCode"],
                'locator': root_el[0].attrib["locator"],
                'text': root_el[0][0].text,
            })
        else:
            raise LaymanError(37, data={
                'response': r.content
            })
    assert root_el.tag == nspath_eval('csw:TransactionResponse', NAMESPACES), r.content
    assert root_el.find(nspath_eval('csw:TransactionSummary/csw:totalInserted', NAMESPACES)).text == "1", r.content

    muuid_els = root_el.findall(nspath_eval('csw:InsertResult/csw:BriefRecord/dc:identifier', NAMESPACES))
    assert len(muuid_els) == 1, r.content
    muuid = muuid_els[0].text
    return muuid

