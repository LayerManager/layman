import os
from owslib.util import nspath_eval
from flask import g, current_app
from io import BytesIO
from owslib.csw import CatalogueServiceWeb
# from xml.etree import ElementTree as ET
from lxml import etree as ET
from layman import settings, LaymanError
from . import PROPERTIES as MICKA_PROPERTIES
from layman.common.metadata import PROPERTIES as COMMON_PROPERTIES
import requests
from copy import deepcopy


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


def get_single_prop_els(parent_el, prop_name):
    micka_prop = MICKA_PROPERTIES[prop_name]
    single_prop_els = parent_el.xpath(micka_prop['xpath_property'], namespaces=NAMESPACES)
    last_prop_el = None
    if len(single_prop_els) == 0 and micka_prop['xpath_property'].find('[') >= 0:
        simple_xpath_property = micka_prop['xpath_property'][:micka_prop['xpath_property'].find('[')]
        single_prop_els = [
            e for e in
            parent_el.xpath(simple_xpath_property, namespaces=NAMESPACES)
        ]
        last_prop_el = single_prop_els[-1] if single_prop_els else None
        single_prop_els = [
            e for e in
            single_prop_els
            if len(e) == 0
        ]
    last_prop_el = single_prop_els[-1] if single_prop_els else last_prop_el
    return single_prop_els, last_prop_el


def fill_xml_template(template_path, prop_values):
    with open(template_path, 'r') as template_file:
        xml_str = template_file.read()
    parser = ET.XMLParser(remove_blank_text=True)
    root_el = ET.fromstring(xml_str.encode('utf-8'), parser=parser)
    for prop_name, prop_value in prop_values.items():
        # print(f'prop_name={prop_name}')
        common_prop = COMMON_PROPERTIES[prop_name]
        micka_prop = MICKA_PROPERTIES[prop_name]
        parent_el = root_el.xpath(micka_prop['xpath_parent'], namespaces=NAMESPACES)[0]
        single_prop_els, last_prop_el = get_single_prop_els(parent_el, prop_name)
        assert len(single_prop_els) > 0 or last_prop_el is not None, f"Element of property {prop_name} not found!"
        single_prop_values = [prop_value] if common_prop['upper_mp'] == '1' else prop_value
        all_new_els = []
        if len(single_prop_els) > len(single_prop_values):
            for idx in range(len(single_prop_values), len(single_prop_els)):
                # print(f'Removing node {idx}')
                e = single_prop_els[idx]
                e.getparent().remove(e)
        elif len(single_prop_values) > len(single_prop_els):
            e = single_prop_els[-1] if single_prop_els else last_prop_el
            for idx in range(len(single_prop_values) - len(single_prop_els)):
                pe = e.getparent()
                # print(f'Adding node {idx}')
                new_el = deepcopy(e)
                if not single_prop_els:
                    all_new_els.append(new_el)
                pe.insert(pe.index(e)+1, new_el)
        if all_new_els:
            single_prop_els = all_new_els
        else:
            single_prop_els, _ = get_single_prop_els(parent_el, prop_name)
        assert len(single_prop_els) == len(single_prop_values), f"{len(single_prop_els)} != {len(single_prop_values)}"
        # print(f"single_prop_values={single_prop_values}")
        for idx, single_prop_el in enumerate(single_prop_els):
            single_prop_value = single_prop_values[idx]
            micka_prop['adjust_property_element'](single_prop_el, single_prop_value)
    return root_el


def fill_xml_template_as_pretty_str(template_path, prop_values):
    root_el = fill_xml_template(template_path, prop_values)
    pretty_str = ET.tostring(root_el, encoding='unicode', pretty_print=True)
    return pretty_str


def fill_xml_template_as_pretty_file_object(template_path, prop_values):
    root_el = fill_xml_template(template_path, prop_values)
    el_tree = ET.ElementTree(root_el)
    file_object = BytesIO()
    el_tree.write(
        file_object,
        encoding='utf-8',
        xml_declaration=True,
        pretty_print=True,
    )
    file_object.seek(0)
    return file_object


def fill_template(template_path, template_values):
    file_object = fill_template_as_pretty_file_object(template_path, template_values)
    return file_object


def fill_template_as_str(template_path, template_values):
    with open(template_path, 'r') as template_file:
        template_str = template_file.read()
    xml_str = template_str.format(**template_values)
    return xml_str


def fill_template_as_el(template_path, template_values):
    xml_str = fill_template_as_str(template_path, template_values)
    parser = ET.XMLParser(remove_blank_text=True)
    root_el = ET.fromstring(xml_str.encode('utf-8'), parser=parser)

    return root_el


def fill_template_as_pretty_file_object(template_path, template_values):
    root_el = fill_template_as_el(template_path, template_values)
    el_tree = ET.ElementTree(root_el)
    file_object = BytesIO()
    el_tree.write(
        file_object,
        encoding='utf-8',
        xml_declaration=True,
        pretty_print=True,
    )
    file_object.seek(0)
    return file_object


def fill_template_as_pretty_str(template_path, template_values):
    root_el = fill_template_as_el(template_path, template_values)
    pretty_str = ET.tostring(root_el, encoding='unicode', pretty_print=True)
    return pretty_str


def create_csw():
    opts = {} if settings.CSW_BASIC_AUTHN is None else {
        'username': settings.CSW_BASIC_AUTHN[0],
        'password': settings.CSW_BASIC_AUTHN[1],
    }
    opts['skip_caps'] = True
    csw = CatalogueServiceWeb(settings.CSW_URL, **opts) if settings.CSW_URL is not None else None
    return csw


def csw_insert(template_values):
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'csw-insert-template.xml')
    xml_str = fill_template_as_str(template_path, template_values)
    # print(f"CSW insert=\n{xml_str}")
    r = requests.post(settings.CSW_URL, auth=settings.CSW_BASIC_AUTHN, data=xml_str.encode('utf-8'))
    # print(f"CSW insert response=\n{r.text}")
    r.raise_for_status()
    root_el = ET.fromstring(r.content)

    def is_record_exists_exception(root_el):
        return len(root_el) == 1 and \
                root_el[0].tag == nspath_eval('ows:Exception', NAMESPACES) and \
                "exceptionCode" in root_el[0].attrib and \
                root_el[0].attrib["exceptionCode"] == 'TransactionFailed' and \
                len(root_el[0]) == 1 and \
                root_el[0][0].tag == nspath_eval('ows:ExceptionText', NAMESPACES) and \
                root_el[0][0].text.startswith('Record exists')

    if root_el.tag == nspath_eval('ows:ExceptionReport', NAMESPACES):
        if is_record_exists_exception(root_el):
            raise LaymanError(36, data={
                'exception_code': root_el[0].attrib["exceptionCode"],
                'locator': root_el[0].attrib["locator"],
                'text': root_el[0][0].text,
            })
        else:
            raise LaymanError(37, data={
                'response': r.text
            })
    assert root_el.tag == nspath_eval('csw:TransactionResponse', NAMESPACES), r.content
    assert root_el.find(nspath_eval('csw:TransactionSummary/csw:totalInserted', NAMESPACES)).text == "1", r.content

    muuid_els = root_el.findall(nspath_eval('csw:InsertResult/csw:BriefRecord/dc:identifier', NAMESPACES))
    assert len(muuid_els) == 1, r.content
    muuid = muuid_els[0].text
    return muuid


def csw_delete(muuid):
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'csw-delete-template.xml')
    template_values = {
        'muuid': muuid
    }
    xml_str = fill_template_as_str(template_path, template_values)
    # print(f"CSW delete request=\n{xml_str}")
    r = requests.post(settings.CSW_URL, auth=settings.CSW_BASIC_AUTHN, data=xml_str.encode('utf-8'))
    # print(f"CSW delete response=\n{r.text}")
    r.raise_for_status()
    root_el = ET.fromstring(r.content)

    def is_record_does_not_exist_exception(root_el):
        return len(root_el) == 1 and \
                root_el[0].tag == nspath_eval('ows:Exception', NAMESPACES) and \
                "exceptionCode" in root_el[0].attrib and \
                root_el[0].attrib["exceptionCode"] == 'TransactionFailed' and \
                len(root_el[0]) == 0 and \
                root_el[0].text is None

    if root_el.tag == nspath_eval('ows:ExceptionReport', NAMESPACES):
        if is_record_does_not_exist_exception(root_el):
            return
        else:
            raise LaymanError(37, data={
                'response': r.text
            })
    assert root_el.tag == nspath_eval('csw:TransactionResponse', NAMESPACES), r.content
    assert root_el.find(nspath_eval('csw:TransactionSummary/csw:totalDeleted', NAMESPACES)).text == "1", r.content


def parse_md_properties(file_obj, properties):
    # print('xml_str', xml_str)
    root_el = ET.parse(file_obj)
    # print(f"root_el={root_el}")
    result = {}
    for prop_name in properties:
        # print(f"prop_name={prop_name}")
        micka_prop = MICKA_PROPERTIES[prop_name]
        common_prop = COMMON_PROPERTIES[prop_name]
        # print(f"prop['xpath_parent']={prop['xpath_parent']}")
        parent_el = root_el.xpath(micka_prop['xpath_parent'], namespaces=NAMESPACES)
        parent_el = parent_el[0] if parent_el else None
        # print(f"prop['xpath_property']={prop['xpath_property']}")
        prop_els = parent_el.xpath(micka_prop['xpath_property'], namespaces=NAMESPACES) if parent_el is not None else []
        # print(f"prop['xpath_extract']={prop['xpath_extract']}")
        # print(f"len(prop_els)={len(prop_els)}")
        prop_values = []
        for prop_el in prop_els:
            prop_value = micka_prop['xpath_extract_fn'](prop_el.xpath(micka_prop['xpath_extract'], namespaces=NAMESPACES))
            if prop_value is not None:
                prop_values.append(prop_value)
        if common_prop['upper_mp'] == '1':
            result[prop_name] = prop_values[0] if prop_values else None
        else:
            result[prop_name] = prop_values
    return result


def prop_equals(value_a, value_b, equals_fn=None):
    equals_fn = equals_fn or (lambda a,b: a==b)
    if value_a is None or value_b is None:
        return value_a is value_b
    else:
        return equals_fn(value_a, value_b)


def prop_equals_or_none(values, equals_fn=None):
    equals_fn = equals_fn or (lambda a,b: a==b)
    values = [v for v in values if v is not None]
    if len(values)<2:
        return True
    result = True
    for idx in range(len(values)-1):
        result = equals_fn(values[idx], values[idx+1])
        if not result:
            break
    return result
