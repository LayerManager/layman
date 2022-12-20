import os
import time
from io import BytesIO
from xml.sax.saxutils import escape
import urllib.parse as urlparse
from copy import deepcopy
import logging
import requests
from owslib.csw import CatalogueServiceWeb
from owslib.util import nspath_eval
from lxml import etree as ET

from layman import settings, authz
from layman.common.metadata import PROPERTIES as COMMON_PROPERTIES
from layman.util import get_publication_info
from micka_util import NAMESPACES
from .requests import base_insert, csw_delete, fill_template_as_str

logger = logging.getLogger(__name__)


for k, v in NAMESPACES.items():
    ET.register_namespace(k, v)


def get_single_prop_els(parent_el, prop_name, publ_properties):
    micka_prop = publ_properties[prop_name]
    single_prop_els = parent_el.xpath(micka_prop['xpath_property'], namespaces=NAMESPACES)
    last_prop_el = None
    if len(single_prop_els) == 0 and micka_prop['xpath_property'].find('[') >= 0:
        simple_xpath_property = micka_prop['xpath_property'][:micka_prop['xpath_property'].find('[')]
        single_prop_els = parent_el.xpath(simple_xpath_property, namespaces=NAMESPACES)
        last_prop_el = single_prop_els[-1] if single_prop_els else None
        single_prop_els = [
            e for e in
            single_prop_els
            if len(e) == 0
        ]
    last_prop_el = single_prop_els[-1] if single_prop_els else last_prop_el
    return single_prop_els, last_prop_el


def read_xml_tree(template_path):
    with open(template_path, 'r') as template_file:
        xml_str = template_file.read()
    parser = ET.XMLParser(remove_blank_text=True)
    tree = ET.fromstring(xml_str.encode('utf-8'), parser=parser)
    return tree


def fill_xml_template(template_path, prop_values, publ_properties):
    tree = read_xml_tree(template_path)
    return fill_xml_template_obj(tree, prop_values, publ_properties)


def fill_xml_template_obj(tree_or_el, prop_values, publ_properties, basic_template_path=None):
    is_el = ET.iselement(tree_or_el)
    tmp_tree = None
    for prop_name, prop_value in prop_values.items():
        # current_app.logger.info(f'prop_name={prop_name}')
        common_prop = COMMON_PROPERTIES[prop_name]
        micka_prop = publ_properties[prop_name]
        xpath_parent = micka_prop['xpath_parent']
        if is_el:
            xpath_parent = micka_prop['xpath_parent'].split('/')[2:]
            xpath_parent.insert(0, '.')
            xpath_parent = '/'.join(xpath_parent)
        parent_el = tree_or_el.xpath(xpath_parent, namespaces=NAMESPACES)
        if len(parent_el) == 0:
            # current_app.logger.info(f"Parent element of property {prop_name} not found, copying from template")
            xpath_parent_parts = xpath_parent.split('[')[0].split('/')
            anc_level_distance = 0
            for idx in reversed(range(len(xpath_parent_parts))):
                anc_level_distance += 1
                last_anc_els = tree_or_el.xpath('/'.join(xpath_parent_parts[:idx]), namespaces=NAMESPACES)
                if len(last_anc_els) > 0:
                    last_anc_el = last_anc_els[0]
                    break
            # print(f"Found ancestor element {last_anc_el.tag}")
            tmp_tree = tmp_tree or read_xml_tree(basic_template_path)
            tmp_parent_el = tmp_tree.xpath(micka_prop['xpath_parent'], namespaces=NAMESPACES)[0]
            tmp_el_to_copy = tmp_parent_el
            while anc_level_distance > 1:
                tmp_el_to_copy = tmp_el_to_copy.getparent()
                anc_level_distance -= 1
            tmp_last_anc_el = tmp_el_to_copy.getparent()
            assert tmp_last_anc_el.tag == last_anc_el.tag
            tmp_prev_sibl = tmp_last_anc_el[tmp_last_anc_el.index(tmp_el_to_copy) - 1]
            prev_sibl = last_anc_el.findall(f"./{tmp_prev_sibl.tag}")[-1]
            insert_idx = last_anc_el.index(prev_sibl) + 1
            last_anc_el.insert(insert_idx, deepcopy(tmp_el_to_copy))

            parent_el = tree_or_el.xpath(xpath_parent, namespaces=NAMESPACES)
        else:
            pass
            # print(f"Parent element of property {prop_name} found.")

        assert len(parent_el) > 0, f"Parent element of property {prop_name} not found!"
        parent_el = parent_el[0]
        single_prop_els, last_prop_el = get_single_prop_els(parent_el, prop_name, publ_properties)
        if common_prop['upper_mp'] == '1':
            single_prop_values = [prop_value]
        elif prop_value is None:
            single_prop_values = []
        elif len(prop_value) == 0 and common_prop.get('lower_mp', None) == '1':
            single_prop_values = [None]
        else:
            single_prop_values = prop_value
        all_new_els = []
        if len(single_prop_els) > 0 or last_prop_el is not None:
            assert len(single_prop_els) > 0 or last_prop_el is not None, f"Element of property {prop_name} not found!"
            if len(single_prop_els) > len(single_prop_values):
                for idx in range(len(single_prop_values), len(single_prop_els)):
                    # print(f'Removing node {idx}')
                    element = single_prop_els[idx]
                    element.getparent().remove(element)
            elif len(single_prop_values) > len(single_prop_els):
                element = single_prop_els[-1] if single_prop_els else last_prop_el
                for idx in range(len(single_prop_values) - len(single_prop_els)):
                    parent_element = element.getparent()
                    # print(f'Adding node {idx}')
                    new_el = deepcopy(element)
                    if not single_prop_els:
                        all_new_els.append(new_el)
                    parent_element.insert(parent_element.index(element) + 1, new_el)
        else:
            # current_app.logger.info(f"Copying property {prop_name} element from template")
            tmp_tree = tmp_tree or read_xml_tree(basic_template_path)
            tmp_parent_el = tmp_tree.xpath(micka_prop['xpath_parent'], namespaces=NAMESPACES)[0]
            tmp_fst_prop_el = tmp_parent_el.xpath(micka_prop['xpath_property'].split('[')[0], namespaces=NAMESPACES)[0]
            # print(f"Found template {prop_name} element {tmp_fst_prop_el.tag}")
            tmp_fst_prop_el_idx = tmp_parent_el.index(tmp_fst_prop_el)
            if tmp_fst_prop_el_idx > 0:
                tmp_prev_sibl = tmp_parent_el[tmp_fst_prop_el_idx - 1]
                prev_sibl = parent_el.findall(f"./{tmp_prev_sibl.tag}")[-1]
                insert_idx = parent_el.index(prev_sibl) + 1
            else:
                insert_idx = 0
            # print(f"Insert Idx of template {prop_name} element: {insert_idx}")
            for idx in range(len(single_prop_values)):
                new_el = deepcopy(tmp_fst_prop_el)
                parent_el.insert(insert_idx, new_el)
                all_new_els.append(new_el)
        if all_new_els:
            single_prop_els = all_new_els
        else:
            single_prop_els, _ = get_single_prop_els(parent_el, prop_name, publ_properties)

        assert len(single_prop_els) == len(single_prop_values), f"{len(single_prop_els)} != {len(single_prop_values)}"
        # print(f"single_prop_values={single_prop_values}")
        for idx, single_prop_el in enumerate(single_prop_els):
            single_prop_value = single_prop_values[idx]
            micka_prop['adjust_property_element'](single_prop_el, single_prop_value)
    return tree_or_el


def fill_xml_template_as_pretty_str(template_path, prop_values, publ_properties):
    root_el = fill_xml_template(template_path, prop_values, publ_properties)
    pretty_str = ET.tostring(root_el, encoding='unicode', pretty_print=True)
    return pretty_str


def fill_xml_template_as_pretty_file_object(template_path, prop_values, publ_properties):
    root_el = fill_xml_template(template_path, prop_values, publ_properties)
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
    root_el, response = base_insert(xml_str)
    assert root_el.tag == nspath_eval('csw:TransactionResponse', NAMESPACES), response.content
    assert root_el.find(nspath_eval('csw:TransactionSummary/csw:totalInserted', NAMESPACES)).text == "1", response.content

    muuid_els = root_el.findall(nspath_eval('csw:InsertResult/csw:BriefRecord/dc:identifier', NAMESPACES))
    assert len(muuid_els) == 1, response.content
    muuid = muuid_els[0].text
    return muuid


def soap_insert(template_values):
    response = None
    try:
        template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'soap-insert-template.xml')
        xml_str = fill_template_as_str(template_path, template_values)
        root_el, response = base_insert(xml_str)
        assert root_el.tag == nspath_eval('soap:Envelope', NAMESPACES), response.content
        assert root_el.find(nspath_eval('soap:Body/csw:TransactionResponse/csw:TransactionSummary/csw:totalInserted',
                                        NAMESPACES)).text == "1", response.content

        muuid_els = root_el.findall(
            nspath_eval('soap:Body/csw:TransactionResponse/csw:InsertResult/csw:BriefRecord/dc:identifier', NAMESPACES))
        assert len(muuid_els) == 1, response.content
        muuid = muuid_els[0].text
    except BaseException as exc:
        if response:
            logger.warning(f'response.content={response.content}')
        raise exc
    return muuid


def soap_insert_record(record, is_public):
    muuid = soap_insert({
        'public': '1' if is_public else '0',
        'record': record,
        'edit_user': settings.CSW_BASIC_AUTHN[0],
        'read_user': settings.CSW_BASIC_AUTHN[0],
    })
    return muuid


def soap_insert_record_from_template(template_path, prop_values, metadata_properties, is_public):
    record = fill_xml_template_as_pretty_str(template_path, prop_values, metadata_properties)
    return soap_insert_record(record, is_public)


def parse_md_properties(file_obj, property_names, publ_properties):
    # print('xml_str', xml_str)
    root_el = ET.parse(file_obj) if type(file_obj) not in [ET._Element, ET._ElementTree] else file_obj  # pylint: disable=protected-access
    root_is_el = ET.iselement(root_el)
    # print(f"root_el={root_el}")
    result = {}
    for prop_name in property_names:
        # print(f"prop_name={prop_name}")
        micka_prop = publ_properties[prop_name]
        common_prop = COMMON_PROPERTIES[prop_name]
        # print(f"prop['xpath_parent']={prop['xpath_parent']}")
        xpath_parent = micka_prop['xpath_parent']
        if root_is_el:
            xpath_parent = micka_prop['xpath_parent'].split('/')[2:]
            xpath_parent.insert(0, '.')
            xpath_parent = '/'.join(xpath_parent)
        parent_el = root_el.xpath(xpath_parent, namespaces=NAMESPACES)
        # print(f"parent_el={parent_el}")
        parent_el = parent_el[0] if parent_el else None
        # print(f"prop['xpath_property']={prop['xpath_property']}")
        prop_els = parent_el.xpath(micka_prop['xpath_property'], namespaces=NAMESPACES) if parent_el is not None else []
        # print(f"prop['xpath_extract']={prop['xpath_extract']}")
        # print(f"len(prop_els)={len(prop_els)}")
        prop_values = []
        for prop_el in prop_els:
            prop_value = micka_prop['xpath_extract_fn'](
                prop_el.xpath(micka_prop['xpath_extract'], namespaces=NAMESPACES))
            if prop_value is not None:
                prop_values.append(prop_value)
        if common_prop['upper_mp'] == '1':
            result[prop_name] = prop_values[0] if prop_values else None
        else:
            result[prop_name] = prop_values
        if common_prop.get('ensure_order') is True:
            result[prop_name].sort()
        if common_prop.get('empty_list_to_none') is True:
            result[prop_name] = result[prop_name] if result[prop_name] else None
    return result


def _clear_el(element):
    element.attrib.clear()
    for child in list(element):
        element.remove(child)


def _add_unknown_reason(element):
    element.attrib[ET.QName(NAMESPACES['gco'], 'nilReason')] = 'unknown'


def adjust_character_string(prop_el, prop_value):
    _clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(
            f"""<gco:CharacterString xmlns:gco="{NAMESPACES['gco']}">{escape(prop_value)}</gco:CharacterString>""")
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_integer(prop_el, prop_value):
    _clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(
            f"""<gco:Integer xmlns:gco="{NAMESPACES['gco']}">{escape(str(prop_value))}</gco:Integer>""")
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_date_string(prop_el, prop_value):
    _clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(f"""<gco:Date xmlns:gco="{NAMESPACES['gco']}">{escape(prop_value)}</gco:Date>""")
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_date_string_with_type(prop_el, prop_value, date_type=None):
    assert date_type is not None
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:CI_Date xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gco="{NAMESPACES['gco']}">
    <gmd:date>
        <gco:Date>{escape(prop_value)}</gco:Date>
    </gmd:date>
    <gmd:dateType>
        <gmd:CI_DateTypeCode codeListValue="{date_type}" codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode">{date_type}</gmd:CI_DateTypeCode>
    </gmd:dateType>
</gmd:CI_Date>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_reference_system_info(prop_el, prop_value):
    _clear_el(prop_el)
    if prop_value is not None:
        prop_epsg, prop_epsg_code = prop_value.upper().split(":")
        assert prop_epsg == 'EPSG'
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:MD_ReferenceSystem xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gmx="{NAMESPACES['gmx']}" xmlns:xlink="{NAMESPACES['xlink']}">
    <gmd:referenceSystemIdentifier>
        <gmd:RS_Identifier>
            <gmd:code>
                <gmx:Anchor xlink:href="http://www.opengis.net/def/crs/EPSG/0/{prop_epsg_code}">{prop_value}</gmx:Anchor>
            </gmd:code>
        </gmd:RS_Identifier>
    </gmd:referenceSystemIdentifier>
</gmd:MD_ReferenceSystem>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_identifier_with_label(prop_el, prop_value):
    _clear_el(prop_el)
    parser = ET.XMLParser(remove_blank_text=True)
    if prop_value is not None:
        identifier = prop_value['identifier']
        label = prop_value['label']
        child_el = ET.fromstring(f"""
<gmd:MD_Identifier xmlns:gmx="{NAMESPACES['gmx']}" xmlns:gmd="{NAMESPACES['gmd']}" xmlns:xlink="{NAMESPACES['xlink']}">
    <gmd:code>
        <gmx:Anchor xlink:href="{identifier}">{escape(label)}</gmx:Anchor>
    </gmd:code>
</gmd:MD_Identifier>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_graphic_url(prop_el, prop_value):
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:MD_BrowseGraphic xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gco="{NAMESPACES['gco']}">
    <gmd:fileName>
        <gco:CharacterString>{escape(prop_value)}</gco:CharacterString>
    </gmd:fileName>
    <gmd:fileType>
        <gco:CharacterString>PNG</gco:CharacterString>
    </gmd:fileType>
</gmd:MD_BrowseGraphic>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_language(prop_el, prop_value):
    _clear_el(prop_el)
    if prop_value is not None:
        child_el = ET.fromstring(
            f"""<gmd:LanguageCode xmlns:gmd="{NAMESPACES['gmd']}" codeListValue=\"{prop_value}\" codeList=\"http://www.loc.gov/standards/iso639-2/\">{prop_value}</gmd:LanguageCode>""")
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_extent(prop_el, prop_value):
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:EX_GeographicBoundingBox xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gco="{NAMESPACES['gco']}">
    <gmd:westBoundLongitude>
        <gco:Decimal>{prop_value[0]}</gco:Decimal>
    </gmd:westBoundLongitude>
    <gmd:eastBoundLongitude>
        <gco:Decimal>{prop_value[2]}</gco:Decimal>
    </gmd:eastBoundLongitude>
    <gmd:southBoundLatitude>
        <gco:Decimal>{prop_value[1]}</gco:Decimal>
    </gmd:southBoundLatitude>
    <gmd:northBoundLatitude>
        <gco:Decimal>{prop_value[3]}</gco:Decimal>
    </gmd:northBoundLatitude>
</gmd:EX_GeographicBoundingBox>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_temporal_element(prop_el, prop_value):
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        el_id = f'TI_{prop_value.replace(":", "-")}'
        child_el = ET.fromstring(f"""
  <gmd:EX_TemporalExtent xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gml="{NAMESPACES['gml']}">
    <gmd:extent>
      <gml:TimeInstant gml:id="{el_id}">
        <gml:timePosition>{prop_value}</gml:timePosition>
      </gml:TimeInstant>
    </gmd:extent>
  </gmd:EX_TemporalExtent>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_online_url(prop_el, prop_value, resource_protocol=None, online_function=None):
    assert resource_protocol is not None
    assert online_function is not None
    _clear_el(prop_el)
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:CI_OnlineResource xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gmx="{NAMESPACES['gmx']}" xmlns:xlink="{NAMESPACES['xlink']}">
    <gmd:linkage>
        <gmd:URL>{escape(prop_value)}</gmd:URL>
    </gmd:linkage>
    <gmd:protocol>
        <gmx:Anchor xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/{resource_protocol}">{resource_protocol}</gmx:Anchor>
    </gmd:protocol>
     <gmd:function>
        <gmd:CI_OnLineFunctionCode codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_OnLineFunctionCode" codeListValue="{online_function}">{online_function}</gmd:CI_OnLineFunctionCode>
     </gmd:function>
</gmd:CI_OnlineResource>
""", parser=parser)
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def adjust_operates_on(prop_el, prop_value):
    _clear_el(prop_el)
    if prop_value is not None:
        prop_el.attrib[ET.QName(NAMESPACES['xlink'], 'href')] = prop_value['xlink:href']
        prop_el.attrib[ET.QName(NAMESPACES['xlink'], 'title')] = prop_value['xlink:title']
        prop_el.attrib[ET.QName(NAMESPACES['xlink'], 'type')] = 'simple'
    else:
        _add_unknown_reason(prop_el)


def extract_spatial_resolution(prop_els):
    result = {}
    if prop_els:
        prop_el = prop_els[0]

        # scale_denominator
        denominator_els = prop_el.xpath('./gmd:MD_Resolution/gmd:equivalentScale/gmd:MD_RepresentativeFraction/'
                                        'gmd:denominator', namespaces=NAMESPACES)
        if denominator_els:
            denominator_el = denominator_els[0]
            scale_strings = denominator_el.xpath('./gco:Integer/text()', namespaces=NAMESPACES)
            scale_denominator = int(scale_strings[0]) if scale_strings else None
            result['scale_denominator'] = scale_denominator

        # ground_sample_distance
        distance_prop_els = prop_el.xpath('./gmd:MD_Resolution/gmd:distance', namespaces=NAMESPACES)
        if distance_prop_els:
            ground_sample_distance = None
            distance_prop_el = distance_prop_els[0]
            distance_value_els = distance_prop_el.xpath('./gco:Distance', namespaces=NAMESPACES)
            if distance_value_els:
                distance_value_el = distance_value_els[0]
                distance_value_strings = distance_value_el.xpath('./text()', namespaces=NAMESPACES)
                uom_strings = distance_value_el.xpath('./@uom', namespaces=NAMESPACES)
                if distance_value_strings and uom_strings:
                    distance_value = float(distance_value_strings[0])
                    uom = str(uom_strings[0])
                    ground_sample_distance = {
                        'value': distance_value,
                        'uom': uom,
                    }
            result['ground_sample_distance'] = ground_sample_distance

    result = result or None
    return result


def adjust_spatial_resolution(prop_el, prop_value):
    _clear_el(prop_el)
    child_el = None
    if prop_value is not None:
        parser = ET.XMLParser(remove_blank_text=True)
        assert set(prop_value.keys()).issubset({'scale_denominator', 'ground_sample_distance'}) and len(prop_value) <= 1
        if 'scale_denominator' in prop_value:
            scale_denominator = prop_value['scale_denominator']
            denominator_el_str = f"""
                <gmd:denominator>
                    <gco:Integer>{str(scale_denominator)}</gco:Integer>
                </gmd:denominator>
            """ if scale_denominator is not None else '<gmd:denominator gco:nilReason="unknown" />'
            child_el = ET.fromstring(f"""
                <gmd:MD_Resolution xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gco="{NAMESPACES['gco']}">
                  <gmd:equivalentScale>
                    <gmd:MD_RepresentativeFraction>
                      {denominator_el_str}
                    </gmd:MD_RepresentativeFraction>
                  </gmd:equivalentScale>
                </gmd:MD_Resolution>
            """, parser=parser)
        if 'ground_sample_distance' in prop_value:
            ground_sample_distance = prop_value['ground_sample_distance']
            if ground_sample_distance is not None:
                distance_value = ground_sample_distance.get('value')
                uom = ground_sample_distance.get('uom')
                assert distance_value is not None and uom is not None
                distance_el_str = f"""
                  <gmd:distance>
                    <gco:Distance uom="{escape(uom)}">{escape(str(distance_value))}</gco:Distance>
                  </gmd:distance>
                """
            else:
                distance_el_str = '<gmd:distance gco:nilReason="unknown" />'
            child_el = ET.fromstring(f"""
                <gmd:MD_Resolution xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gco="{NAMESPACES['gco']}">
                  {distance_el_str}
                </gmd:MD_Resolution>
            """, parser=parser)
    if child_el is not None:
        prop_el.append(child_el)
    else:
        _add_unknown_reason(prop_el)


def get_record_element_by_id(csw, ident):
    csw.getrecordbyid(id=[ident], esn='full', outputschema=NAMESPACES['gmd'])
    xml = csw._exml  # pylint: disable=protected-access
    els = xml.xpath(f"//gmd:MD_Metadata[gmd:fileIdentifier/gco:CharacterString/text() = '{ident}']", namespaces=NAMESPACES)
    # current_app.logger.info(f"Number of md records id={id}: {len(els)}")
    result = els[0] if len(els) > 0 else None
    return result


def get_number_of_records(record_id, use_authn):
    authn = settings.CSW_BASIC_AUTHN if use_authn else None
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'csw-number-of-records-template.xml')
    xml_str = fill_template_as_str(template_path, {'record_id': record_id})

    response = requests.post(settings.CSW_URL,
                             auth=authn,
                             data=xml_str,
                             timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                             )
    response.raise_for_status()
    parser = ET.XMLParser(remove_blank_text=True)
    tree = ET.fromstring(response.text.encode('utf-8'), parser=parser)
    num_records = int(tree.xpath("/csw:GetRecordsResponse/csw:SearchResults/@numberOfRecordsMatched", namespaces=NAMESPACES)[0])
    return num_records


def get_muuid_from_operates_on_link(operates_on_link):
    link_url = urlparse.urlparse(operates_on_link)
    return urlparse.parse_qs(link_url.query)['ID'][0]


def operates_on_values_to_muuids(operates_on_values):
    return [
        get_muuid_from_operates_on_link(operates_on['xlink:href'])
        for operates_on in operates_on_values
    ]


def is_soap_visibility_change_needed(muuid, access_rights):
    maybe_needed = access_rights is not None and 'read' in access_rights
    if maybe_needed:
        new_is_public = authz.is_user_in_access_rule(settings.RIGHTS_EVERYONE_ROLE, access_rights['read'])
        old_is_public = get_number_of_records(muuid, False) > 0
        needed = new_is_public != old_is_public
    else:
        needed = False
    return needed


def patch_publication_by_soap(workspace,
                              publ_type,
                              publ_name,
                              metadata_properties_to_refresh,
                              actor_name,
                              access_rights,
                              csw_source,
                              csw_patch_method,
                              soap_insert_method):
    publ_info = get_publication_info(workspace, publ_type, publ_name, context={'keys': ['access_rights'], })
    uuid = publ_info.get('uuid')

    csw_instance = create_csw()
    if uuid is None or csw_instance is None:
        return
    muuid = csw_source.get_metadata_uuid(uuid)
    num_records = get_number_of_records(muuid, True)
    if num_records == 0:
        full_access_rights = authz.complete_access_rights(access_rights, publ_info['access_rights'])
        soap_insert_method(workspace, publ_name, full_access_rights, actor_name)
    else:
        use_soap = is_soap_visibility_change_needed(muuid, access_rights)
        if use_soap:
            csw_delete(muuid)
            time.sleep(1)
            soap_insert_method(workspace, publ_name, access_rights, actor_name)
        else:
            csw_patch_method(workspace, publ_name, metadata_properties_to_refresh, actor_name)
