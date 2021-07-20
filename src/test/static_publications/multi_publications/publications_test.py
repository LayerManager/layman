import pytest
from layman import app, util as layman_util
from test_tools import process_client
from ... import static_publications as data
from ..data import ensure_publication


@pytest.mark.parametrize('context, expected_publications', [
    ({'actor_name': 'test_get_publication_infos_user_actor', 'access_type': 'read'}, {'post_public_sld', 'post_private_write_sld'},),
    ({'actor_name': 'test_get_publication_infos_user_actor', 'access_type': 'write'}, {'post_public_sld'},),
], )
@pytest.mark.usefixtures('liferay_mock', 'ensure_layman',)
def test_get_publication_infos(context,
                               expected_publications):
    ensure_publication(data.OWNER, process_client.LAYER_TYPE, 'post_private_sld')
    ensure_publication(data.OWNER, process_client.LAYER_TYPE, 'post_private_write_sld')
    ensure_publication(data.OWNER, process_client.LAYER_TYPE, 'post_public_sld')

    with app.app_context():
        infos = layman_util.get_publication_infos(data.OWNER, process_client.LAYER_TYPE, context)
    publ_set = set(publication_name for (workspace, publication_type, publication_name) in infos.keys())
    assert expected_publications.issubset(publ_set), publ_set