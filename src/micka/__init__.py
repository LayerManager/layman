from lxml import etree as ET
import requests

MICKA_HTTP_TIMEOUT = None
NAMESPACES = {
    'csw': 'http://www.opengis.net/cat/csw/2.0.2',
    'ows': 'http://www.opengis.net/ows/1.1',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
    'gml': 'http://www.opengis.net/gml/3.2',
    'gmx': 'http://www.isotc211.org/2005/gmx',
    'xlink': 'http://www.w3.org/1999/xlink',
    'srv': 'http://www.isotc211.org/2005/srv',
    'soap': 'http://www.w3.org/2003/05/soap-envelope',
    'hs': 'http://www.hsrs.cz/micka',
}


def set_settings(timeout):
    # pylint: disable=global-statement
    global MICKA_HTTP_TIMEOUT

    MICKA_HTTP_TIMEOUT = timeout


def csw_get_records(csw_url, *, auth):
    resp = requests.post(csw_url, auth=auth, data=f"""
        <csw:GetRecords xmlns:ogc="http://www.opengis.net/ogc" xmlns:csw="http://www.opengis.net/cat/csw/2.0.2" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dct="http://purl.org/dc/terms/" xmlns:ows="http://www.opengis.net/ows" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:apiso="http://www.opengis.net/cat/csw/apiso/1.0" xmlns:gmd="http://www.isotc211.org/2005/gmd" outputSchema="http://www.isotc211.org/2005/gmd" maxRecords="100" startPosition="1" outputFormat="application/xml" service="CSW" resultType="results" version="2.0.2" requestId="1" debug="0">
         <csw:Query typeNames="gmd:MD_Metadata">
          <csw:ElementSetName>summary</csw:ElementSetName>
          <csw:Constraint version="1.1.0">
           <ogc:Filter xmlns:gml="http://www.opengis.net/gml">
             <ogc:PropertyIsLike wildCard="*" singleChar="@" escapeChar="\\">
               <ogc:PropertyName>apiso:Identifier</ogc:PropertyName>
               <ogc:Literal>*</ogc:Literal>
             </ogc:PropertyIsLike>
           </ogc:Filter>
          </csw:Constraint>
         </csw:Query>
        </csw:GetRecords>
        """, timeout=MICKA_HTTP_TIMEOUT)
    root = ET.fromstring(resp.text.encode('utf-8'))
    els = root.xpath(f"/csw:GetRecordsResponse/csw:SearchResults/gmd:MD_Metadata", namespaces=NAMESPACES)
    return els


def csw_get_record_ids_containing_url(csw_url, *, contained_url_part, auth):
    els = csw_get_records(csw_url, auth=auth)
    els = [
        el for el in els
        if any(contained_url_part in online_url
               for online_url in
               el.xpath(
                   f"./gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()",
                   namespaces=NAMESPACES)
               )
    ]
    return [el.xpath(f"./gmd:fileIdentifier/gco:CharacterString/text()", namespaces=NAMESPACES)[0] for el in els]
