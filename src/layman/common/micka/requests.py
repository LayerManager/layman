import os

from lxml import etree as ET
from owslib.util import nspath_eval

from layman import settings, LaymanError
import requests_util.retry
from micka import NAMESPACES


def is_record_exists_exception(root_el):
    return len(root_el) == 1 and \
        root_el[0].tag == nspath_eval('ows:Exception', NAMESPACES) and \
        "exceptionCode" in root_el[0].attrib and \
        root_el[0].attrib["exceptionCode"] == 'TransactionFailed' and \
        len(root_el[0]) == 1 and \
        root_el[0][0].tag == nspath_eval('ows:ExceptionText', NAMESPACES) and \
        root_el[0][0].text.startswith('Record exists')


def is_record_does_not_exist_exception(root_el):
    return len(root_el) == 1 and \
        root_el[0].tag == nspath_eval('ows:Exception', NAMESPACES) and \
        "exceptionCode" in root_el[0].attrib and \
        root_el[0].attrib["exceptionCode"] == 'TransactionFailed' and \
        len(root_el[0]) == 0 and \
        root_el[0].text is None


def base_insert(xml_str):
    # print(f"Micka insert=\n{xml_str}")
    response = requests_util.retry.get_session().post(settings.CSW_URL,
                                                      auth=settings.CSW_BASIC_AUTHN,
                                                      data=xml_str.encode('utf-8'),
                                                      timeout=settings.DEFAULT_CONNECTION_TIMEOUT, )
    # print(f"Micka insert response=\n{r.text}")
    response.raise_for_status()
    root_el = ET.fromstring(response.content)

    if root_el.tag == nspath_eval('ows:ExceptionReport', NAMESPACES):
        if is_record_exists_exception(root_el):
            raise LaymanError(36, data={
                'exception_code': root_el[0].attrib["exceptionCode"],
                'locator': root_el[0].attrib["locator"],
                'text': root_el[0][0].text,
            })
        raise LaymanError(37, data={
            'response': response.text
        })
    return root_el, response


def csw_update(template_values, timeout=None):
    timeout = timeout or settings.DEFAULT_CONNECTION_TIMEOUT
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'csw-update-template.xml')
    xml_str = fill_template_as_str(template_path, template_values)
    # print(f"CSW update request=\n{xml_str}")
    response = requests_util.retry.get_session().post(settings.CSW_URL,
                                                      auth=settings.CSW_BASIC_AUTHN,
                                                      data=xml_str.encode('utf-8'),
                                                      timeout=timeout,
                                                      )
    # print(f"CSW update response=\n{r.text}")
    response.raise_for_status()
    root_el = ET.fromstring(response.content)

    if root_el.tag == nspath_eval('ows:ExceptionReport', NAMESPACES):
        if is_record_does_not_exist_exception(root_el):
            raise LaymanError(39, data={
                'response': response.text
            })
        raise LaymanError(37, data={
            'response': response.text
        })
    assert root_el.tag == nspath_eval('csw:TransactionResponse', NAMESPACES), response.content
    assert root_el.find(nspath_eval('csw:TransactionSummary/csw:totalUpdated', NAMESPACES)).text == "1", response.content


def csw_delete(muuid):
    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'csw-delete-template.xml')
    template_values = {
        'muuid': muuid
    }
    xml_str = fill_template_as_str(template_path, template_values)
    # print(f"CSW delete request=\n{xml_str}")
    response = requests_util.retry.get_session().post(settings.CSW_URL,
                                                      auth=settings.CSW_BASIC_AUTHN,
                                                      data=xml_str.encode('utf-8'),
                                                      timeout=settings.DEFAULT_CONNECTION_TIMEOUT,
                                                      )
    # print(f"CSW delete response=\n{r.text}")
    response.raise_for_status()
    root_el = ET.fromstring(response.content)

    if root_el.tag == nspath_eval('ows:ExceptionReport', NAMESPACES):
        if is_record_does_not_exist_exception(root_el):
            return
        raise LaymanError(37, data={
            'response': response.text
        })
    assert root_el.tag == nspath_eval('csw:TransactionResponse', NAMESPACES), response.content
    assert root_el.find(nspath_eval('csw:TransactionSummary/csw:totalDeleted', NAMESPACES)).text == "1", response.content


def fill_template_as_str(template_path, template_values):
    with open(template_path, 'r', encoding="utf-8") as template_file:
        template_str = template_file.read()
    xml_str = template_str.format(**template_values)
    return xml_str
