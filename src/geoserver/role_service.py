import logging
import os
import shutil
import sys
from urllib.parse import urlparse
from xml.sax.saxutils import escape
import psycopg2

from db import util as db_util
from requests_util import url_util
from . import authn

logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


ROLE_SERVICE_PATH = 'security/role/'
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def setup_jdbc_role_service(data_dir, service_url, role_service_name, db_schema):
    logger.info(f"Ensuring GeoServer DB role service '{role_service_name}' "
                f"for URL: {url_util.redact_uri(service_url)}.")

    role_service_path = os.path.join(data_dir, ROLE_SERVICE_PATH)
    layman_role_service_path = os.path.join(role_service_path, role_service_name)
    if os.path.exists(layman_role_service_path):
        shutil.rmtree(layman_role_service_path)
    source_path = os.path.join(DIRECTORY, 'jdbc_role_service')
    os.mkdir(layman_role_service_path)

    parsed_url = urlparse(service_url)

    with open(os.path.join(source_path, 'config.xml'), encoding="utf-8") as file:
        config_content = file.read()
    with open(os.path.join(layman_role_service_path, 'config.xml'), "w", encoding="utf-8") as file:
        file.write(config_content.format(
            connection_string=f'jdbc:{escape(url_util.redact_uri(service_url, remove_username=True))}',
            username=escape(parsed_url.username),
            password=escape(parsed_url.password),
        ))

    with open(os.path.join(source_path, 'rolesddl.xml'), encoding="utf-8") as file:
        rolesddl_content = file.read()
    with open(os.path.join(layman_role_service_path, 'rolesddl.xml'), "w", encoding="utf-8") as file:
        file.write(rolesddl_content.format(
            schema=escape(db_schema),
        ))

    with open(os.path.join(source_path, 'rolesdml.xml'), encoding="utf-8") as file:
        rolesdml_content = file.read()
    with open(os.path.join(layman_role_service_path, 'rolesdml.xml'), "w", encoding="utf-8") as file:
        file.write(rolesdml_content.format(
            schema=escape(db_schema),
        ))


def set_primary_role_service(data_dir, role_service_name):
    security_xml = authn.get_security(data_dir)
    element = security_xml.find('roleServiceName')
    element.text = role_service_name
    security_path = os.path.join(data_dir, 'security/config.xml')
    security_xml.write(security_path)


def check_jdbc_role_service(role_service_db_uri, role_service_schema):

    try:
        db_util.get_connection_pool(db_uri_str=role_service_db_uri, encapsulate_exception=False)
    except psycopg2.OperationalError as exc:
        secret_conn_dict = url_util.redact_uri(role_service_db_uri)
        raise Exception(f"Failed to connect to role service database {secret_conn_dict}") from exc

    try:
        db_util.run_query(f"select name, parent from {role_service_schema}.roles limit 0",
                          uri_str=role_service_db_uri, encapsulate_exception=False)
        db_util.run_query(f"select username, rolename from {role_service_schema}.user_roles limit 0",
                          uri_str=role_service_db_uri, encapsulate_exception=False)
        db_util.run_query(f"select rolename, propname, propvalue from {role_service_schema}.role_props limit 0",
                          uri_str=role_service_db_uri, encapsulate_exception=False)
        db_util.run_query(f"select groupname, rolename from {role_service_schema}.group_roles limit 0",
                          uri_str=role_service_db_uri, encapsulate_exception=False)
    except BaseException as exc:
        secret_conn_dict = url_util.redact_uri(role_service_db_uri)
        raise Exception(f"Error querying role service database {secret_conn_dict}") from exc
