import pytest

import requests_util.url_util


@pytest.mark.parametrize('uri, remove_username, exp_redact_uri', [
    ('mysql://docker:docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', False,
     'mysql://docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
    ('mysql://docker:@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', False,
     'mysql://docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
    ('mysql://docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', False,
     'mysql://docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
    ('mysql://postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', False,
     'mysql://postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
    ('mysql://docker:docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', True,
     'mysql://postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
    ('mysql://docker:@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', True,
     'mysql://postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
    ('mysql://docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', True,
     'mysql://postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
    ('mysql://postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry', True,
     'mysql://postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
])
def test_redact_uri(uri, remove_username, exp_redact_uri):
    redact_table_uri = requests_util.url_util.redact_uri(uri, remove_username=remove_username)
    assert redact_table_uri == exp_redact_uri
