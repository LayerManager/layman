import pytest

import requests_util.url_util


@pytest.mark.parametrize('uri, exp_redact_uri', [
    ('mysql://docker:docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry',
     'mysql://docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
    ('mysql://docker:@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry',
     'mysql://docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
    ('mysql://docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry',
     'mysql://docker@postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
    ('mysql://postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry',
     'mysql://postgresql:5432/external_test_db?table=table_name&geo_column=wkb_geometry'),
])
def test_redact_uri(uri, exp_redact_uri):
    redact_table_uri = requests_util.url_util.redact_uri(uri)
    assert redact_table_uri == exp_redact_uri
