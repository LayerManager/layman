import pytest
from layman import app
from layman.util import get_publication_info
from ... import static_data as data
from ..data import ensure_all_publications


@pytest.mark.timeout(600)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_find_maps_containing_layer():
    ensure_all_publications()

    for l_workspace, l_type, layer in data.LIST_LAYERS:
        expected_maps = {(workspace, publication)
                         for (workspace, publ_type, publication), values in data.PUBLICATIONS.items()
                         if publ_type == data.MAP_TYPE and (l_workspace, l_type, layer) in values[data.TEST_DATA].get('layers', [])}

        with app.app_context():
            result_maps = {
                (mo['workspace'], mo['name'])
                for mo in get_publication_info(l_workspace, l_type, layer, context={'keys': ['layer_maps']})['_layer_maps']
            }
        assert result_maps == expected_maps
