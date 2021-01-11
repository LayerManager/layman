import sys
import pytest
import requests

del sys.modules['layman']

from layman import app, settings
from .prime_db_schema import table as prime_table
from .filesystem import uuid
from . import LAYER_TYPE
from layman import util as layman_util
from test import process_client, util as test_util


@pytest.mark.usefixtures('ensure_layman')
def test_get_publication_infos():
    username = 'test_get_publication_infos_user'
    layername = 'test_get_publication_infos_layer'
    layertitle = "Test get publication infos - layer íářžý"

    process_client.publish_layer(username, layername, title=layertitle)

    with app.app_context():
        result_infos_all = {layername: {'name': layername,
                                        'title': layertitle,
                                        'uuid': uuid.get_layer_uuid(username, layername),
                                        'type': LAYER_TYPE,
                                        'access_rights': {'read': [settings.RIGHTS_EVERYONE_ROLE, ],
                                                          'write': [settings.RIGHTS_EVERYONE_ROLE, ],
                                                          }
                                        }}
        modules = [
            {'name': 'prime_table.table',
             'result_infos': result_infos_all,
             'method_publications': prime_table.get_publication_infos,
             },
        ]

        for module in modules:
            publication_infos = module["method_publications"](username, LAYER_TYPE)
            test_util.assert_same_infos(publication_infos, module["result_infos"], module)

        # util
        layer_infos = layman_util.get_publication_infos(username, LAYER_TYPE)
        test_util.assert_same_infos(layer_infos, result_infos_all)

    process_client.delete_layer(username, layername)


@pytest.mark.usefixtures('ensure_layman')
def test_get_layer_title():
    username = 'test_get_layer_title_user'
    layers = [("c_test_get_layer_title_layer", "C Test get layer title - map layer íářžý"),
              ("a_test_get_layer_title_layer", "A Test get layer title - map layer íářžý"),
              ("b_test_get_layer_title_layer", "B Test get layer title - map layer íářžý")
              ]
    sorted_layers = sorted(layers)

    for (name, title) in layers:
        process_client.publish_layer(username, name, title=title)

    # layers.GET
    with app.app_context():
        url = layman_util.url_for('rest_layers.get', username=username)
    rv = requests.get(url)
    assert rv.status_code == 200, rv.text

    for i in range(0, len(sorted_layers) - 1):
        assert rv.json()[i]["name"] == sorted_layers[i][0]
        assert rv.json()[i]["title"] == sorted_layers[i][1]

    for (name, title) in layers:
        process_client.delete_layer(username, name)
