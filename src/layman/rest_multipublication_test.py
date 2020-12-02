import pytest
import json
import requests

from layman import app
from layman.util import url_for
from test import process, process_client

ensure_layman = process.ensure_layman
liferay_mock = process.liferay_mock


class TestDeletePublicationsClass:
    owner = 'test_delete_publications_owner'
    deleter = 'test_delete_publications_deleter'
    authn_headers_owner = process_client.get_authz_headers(owner)
    authn_headers_deleter = process_client.get_authz_headers(deleter)

    @pytest.fixture(scope="class")
    def provide_data(self):
        process_client.ensure_reserved_username(self.owner, self.authn_headers_owner)
        process_client.ensure_reserved_username(self.deleter, self.authn_headers_deleter)
        yield

    @pytest.mark.parametrize("publication_prefix, publish_method, get_url_string, delete_url_string", [
        ('test_delete_publications_layer', process_client.publish_layer, 'rest_layers.get', 'rest_layers.delete', ),
        ('test_delete_publications_map', process_client.publish_map, 'rest_maps.get', 'rest_maps.delete',),
    ])
    @pytest.mark.usefixtures('liferay_mock', 'ensure_layman', 'provide_data')
    def test_delete_publications(self,
                                 publication_prefix,
                                 publish_method,
                                 get_url_string,
                                 delete_url_string):
        owner = self.owner
        authn_headers_owner = self.authn_headers_owner
        authn_headers_deleter = self.authn_headers_deleter

        publication_a = publication_prefix + '_a'
        publication_b = publication_prefix + '_b'
        publications = [(publication_a, {'read': 'EVERYONE', 'write': owner}),
                        (publication_b, {'read': 'EVERYONE', 'write': 'EVERYONE'}),
                        ]

        for (name, access_rights) in publications:
            publish_method(owner, name, access_rights=access_rights, headers=authn_headers_owner)

        with app.app_context():
            url_get = url_for(get_url_string, username=owner)
            url_del = url_for(delete_url_string, username=owner)

        rv = requests.get(url_get, headers=authn_headers_owner)
        assert rv.status_code == 200, rv.text
        assert len(rv.json()) == len(publications)

        # Delete by other user with rights only for one layer
        rv = requests.delete(url_del, headers=authn_headers_deleter)
        assert rv.status_code == 200, rv.text
        publications = {publication['name'] for publication in json.loads(rv.text)}
        assert {publication_b, } == publications

        rv = requests.get(url_get, headers=authn_headers_owner)
        assert rv.status_code == 200, rv.text
        publications = {publication['name'] for publication in json.loads(rv.text)}
        assert {publication_a, } == publications

        # Delete by owner
        rv = requests.delete(url_del, headers=authn_headers_owner)
        assert rv.status_code == 200, rv.text
        publications = {publication['name'] for publication in json.loads(rv.text)}
        assert {publication_a, } == publications

        # Check, that everything is deleted
        rv = requests.get(url_get, headers=authn_headers_owner)
        assert rv.status_code == 200, rv.text
        publications = {publication['name'] for publication in json.loads(rv.text)}
        assert set() == publications
