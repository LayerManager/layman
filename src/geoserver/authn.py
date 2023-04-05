import logging
import os
import pathlib
from lxml import etree as ET

from setup_geoserver import logger

logger = logging.getLogger(__name__)


def ensure_request_header_authn(data_dir, name, attribute, user_group_service, role_service):
    authn_exists = get_authn(data_dir, name) is not None
    if not authn_exists:
        create_request_header_authn(data_dir, name, attribute, user_group_service, role_service)
    authn_created = not authn_exists
    return authn_created


def create_request_header_authn(data_dir, name, attribute, user_group_service, role_service):
    logger.info(f"Creating Request Header Authentication '{name}'")
    file_path = os.path.join(data_dir, 'security/filter', name, 'config.xml')
    pathlib.Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
    with open(file_path, "x", encoding="utf-8") as file:
        file.write(f'''<requestHeaderAuthentication>
  <id>-7ae6319c:1744eafb853:-7f6d</id>
  <name>{name}</name>
  <className>org.geoserver.security.filter.GeoServerRequestHeaderAuthenticationFilter</className>
  <roleSource class="org.geoserver.security.config.PreAuthenticatedUserNameFilterConfig$PreAuthenticatedUserNameRoleSource">RoleService</roleSource>
  <userGroupServiceName>{user_group_service}</userGroupServiceName>
  <roleServiceName>{role_service}</roleServiceName>
  <principalHeaderAttribute>{attribute}</principalHeaderAttribute>
</requestHeaderAuthentication>''')


def get_authn(data_dir, name):
    file_path = os.path.join(data_dir, 'security/filter', name, 'config.xml')
    try:
        return ET.parse(file_path)
    except OSError:
        return None


def get_security(data_dir):
    security_path = os.path.join(data_dir, 'security/config.xml')
    security_xml = ET.parse(security_path)
    return security_xml


def get_security_filter_group(data_dir, name):
    security_xml = get_security(data_dir)
    filter_group_el = security_xml.find(f"//filters[@name='{name}']")
    return filter_group_el


def create_security_filter_group(data_dir, name, filter_names):
    logger.info(f"  Creating Authentication Filter group '{name}' with filters {','.join(filter_names)}")
    security_xml = get_security(data_dir)
    new_chain = ET.Element('filters')
    new_chain.attrib['name'] = name
    new_chain.attrib['class'] = 'org.geoserver.security.ServiceLoginFilterChain'
    new_chain.attrib['interceptorName'] = 'interceptor'
    new_chain.attrib['exceptionTranslationName'] = 'exception'
    new_chain.attrib['path'] = '/**/wfs,/**/wms,/**/ows'
    new_chain.attrib['disabled'] = 'false'
    new_chain.attrib['allowSessionCreation'] = 'false'
    new_chain.attrib['ssl'] = 'false'
    new_chain.attrib['matchHTTPMethod'] = 'false'
    for filter_name in filter_names:
        new_filter = ET.SubElement(new_chain, 'filter')
        new_filter.text = filter_name
    filter_chain = security_xml.find(f"//filterChain")
    filter_chain.insert(0, new_chain)
    security_path = os.path.join(data_dir, 'security/config.xml')
    security_xml.write(security_path)


def remove_security_filter_groups(data_dir, names):
    security_xml = get_security(data_dir)

    for name in names:
        filter = security_xml.find(f'//filterChain/filters[@name="{name}"]')
        if filter:
            logger.info(f"  Deleting Authentication Filter groups '{name}'")
            filter.getparent().remove(filter)
    security_path = os.path.join(data_dir, 'security/config.xml')
    security_xml.write(security_path)


def ensure_security_filter_group(data_dir, name, filter_names):
    group_exists = get_security_filter_group(data_dir, name) is not None
    if not group_exists:
        create_security_filter_group(data_dir, name, filter_names)
    group_created = not group_exists
    return group_created


def setup_authn(datadir,
                filter_name,
                header_name,
                header_attribute,
                user_group_service,
                role_service,
                old_filter_names,
                ):
    logger.info(f"Ensuring Authentication Filter group '{filter_name}' "
                f"with filters {header_name}, "
                f"removing old groups {old_filter_names}.")

    ensure_request_header_authn(
        datadir,
        header_name,
        header_attribute,
        user_group_service,
        role_service
    )

    remove_security_filter_groups(
        datadir,
        old_filter_names,
    )

    ensure_security_filter_group(
        datadir,
        filter_name,
        [
            header_name,
            'basic',
            'anonymous',
        ]
    )
