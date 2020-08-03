import os
from owslib.util import nspath_eval
from flask import g, current_app
from io import BytesIO
from owslib.csw import CatalogueServiceWeb
from xml.sax.saxutils import escape
from lxml import etree as ET
from layman import settings, LaymanError
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
    'srv': 'http://www.isotc211.org/2005/srv',
    'soap': 'http://www.w3.org/2003/05/soap-envelope',
    'hs': 'http://www.hsrs.cz/micka',
}
for k, v in NAMESPACES.items():
    ET.register_namespace(k, v)


def get_single_prop_els(parent_el, prop_name, publ_properties):
    micka_prop = publ_properties[prop_name]
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
    is_el = type(tree_or_el) == ET._Element
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
            assert (tmp_last_anc_el.tag == last_anc_el.tag)
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
                    pe.insert(pe.index(e) + 1, new_el)
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


def is_record_exists_exception(root_el):
    return len(root_el) == 1 and \
        root_el[0].tag == nspath_eval('ows:Exception', NAMESPACES) and \
        "exceptionCode" in root_el[0].attrib and \
        root_el[0].attrib["exceptionCode"] == 'TransactionFailed' and \
        len(root_el[0]) == 1 and \
        root_el[0][0].tag == nspath_eval('ows:ExceptionText', NAMESPACES) and \
        root_el[0][0].text.startswith('Record exists')


def base_insert(xml_str):
    # print(f"Micka insert=\n{xml_str}")
    r = requests.post(settings.CSW_URL, auth=settings.CSW_BASIC_AUTHN, data=xml_str.encode('utf-8'))
    # print(f"Micka insert response=\n{r.text}")
    r.raise_for_status()
    root_el = ET.fromstring(r.content)

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
    return root_el, r


def csw_insert(template_values):
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'csw-insert-template.xml')
    xml_str = fill_template_as_str(template_path, template_values)
    root_el, r = base_insert(xml_str)
    assert root_el.tag == nspath_eval('csw:TransactionResponse', NAMESPACES), r.content
    assert root_el.find(nspath_eval('csw:TransactionSummary/csw:totalInserted', NAMESPACES)).text == "1", r.content

    muuid_els = root_el.findall(nspath_eval('csw:InsertResult/csw:BriefRecord/dc:identifier', NAMESPACES))
    assert len(muuid_els) == 1, r.content
    muuid = muuid_els[0].text
    return muuid


def soap_insert(template_values):
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'soap-insert-template.xml')
    xml_str = fill_template_as_str(template_path, template_values)
    root_el, r = base_insert(xml_str)
    assert root_el.tag == nspath_eval('soap:Envelope', NAMESPACES), r.content
    assert root_el.find(nspath_eval('soap:Body/csw:TransactionResponse/csw:TransactionSummary/csw:totalInserted',
                                    NAMESPACES)).text == "1", r.content

    muuid_els = root_el.findall(
        nspath_eval('soap:Body/csw:TransactionResponse/csw:InsertResult/csw:BriefRecord/dc:identifier', NAMESPACES))
    assert len(muuid_els) == 1, r.content
    muuid = muuid_els[0].text
    return muuid


def csw_update(template_values):
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'csw-update-template.xml')
    xml_str = fill_template_as_str(template_path, template_values)
    # print(f"CSW update request=\n{xml_str}")
    r = requests.post(settings.CSW_URL, auth=settings.CSW_BASIC_AUTHN, data=xml_str.encode('utf-8'))
    # print(f"CSW update response=\n{r.text}")
    r.raise_for_status()
    root_el = ET.fromstring(r.content)

    if root_el.tag == nspath_eval('ows:ExceptionReport', NAMESPACES):
        if is_record_does_not_exist_exception(root_el):
            raise LaymanError(39, data={
                'response': r.text
            })
        else:
            raise LaymanError(37, data={
                'response': r.text
            })
    assert root_el.tag == nspath_eval('csw:TransactionResponse', NAMESPACES), r.content
    assert root_el.find(nspath_eval('csw:TransactionSummary/csw:totalUpdated', NAMESPACES)).text == "1", r.content


def is_record_does_not_exist_exception(root_el):
    return len(root_el) == 1 and \
        root_el[0].tag == nspath_eval('ows:Exception', NAMESPACES) and \
        "exceptionCode" in root_el[0].attrib and \
        root_el[0].attrib["exceptionCode"] == 'TransactionFailed' and \
        len(root_el[0]) == 0 and \
        root_el[0].text is None


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

    if root_el.tag == nspath_eval('ows:ExceptionReport', NAMESPACES):
        if is_record_does_not_exist_exception(root_el):
            return
        else:
            raise LaymanError(37, data={
                'response': r.text
            })
    assert root_el.tag == nspath_eval('csw:TransactionResponse', NAMESPACES), r.content
    assert root_el.find(nspath_eval('csw:TransactionSummary/csw:totalDeleted', NAMESPACES)).text == "1", r.content


def parse_md_properties(file_obj, property_names, publ_properties):
    # print('xml_str', xml_str)
    root_el = ET.parse(file_obj) if type(file_obj) not in [ET._Element, ET._ElementTree] else file_obj
    root_is_el = type(root_el) == ET._Element
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
    return result


def _clear_el(el):
    el.attrib.clear()
    for child in list(el):
        el.remove(child)


def _add_unknown_reason(el):
    el.attrib[ET.QName(NAMESPACES['gco'], 'nilReason')] = 'unknown'


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
        parser = ET.XMLParser(remove_blank_text=True)
        child_el = ET.fromstring(f"""
<gmd:MD_ReferenceSystem xmlns:gmd="{NAMESPACES['gmd']}" xmlns:gmx="{NAMESPACES['gmx']}" xmlns:xlink="{NAMESPACES['xlink']}">
    <gmd:referenceSystemIdentifier>
        <gmd:RS_Identifier>
            <gmd:code>
                <gmx:Anchor xlink:href="http://www.opengis.net/def/crs/EPSG/0/{prop_value}">EPSG:{prop_value}</gmx:Anchor>
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


def get_record_element_by_id(csw, id):
    csw.getrecordbyid(id=[id], esn='full', outputschema=NAMESPACES['gmd'])
    xml = csw._exml
    els = xml.xpath(f"//gmd:MD_Metadata[gmd:fileIdentifier/gco:CharacterString/text() = '{id}']", namespaces=NAMESPACES)
    # current_app.logger.info(f"Number of md records id={id}: {len(els)}")
    result = els[0] if len(els) > 0 else None
    return result
