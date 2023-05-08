import uuid
import pytest

from layman import app, settings, util as layman_util
from layman.common.prime_db_schema import publications as pubs_util
from .wfs_wms_status import set_after_restart
from .. import LAYER_TYPE


@pytest.mark.parametrize('wfs_wms_status_before, wfs_wms_status_after', [
    pytest.param(
        settings.EnumWfsWmsStatus.PREPARING,
        settings.EnumWfsWmsStatus.NOT_AVAILABLE,
        id='layer_preparing',
    ),
    pytest.param(
        settings.EnumWfsWmsStatus.AVAILABLE,
        settings.EnumWfsWmsStatus.AVAILABLE,
        id='layer_available',
    ),
    pytest.param(
        settings.EnumWfsWmsStatus.NOT_AVAILABLE,
        settings.EnumWfsWmsStatus.NOT_AVAILABLE,
        id='layer_not_available',
    ),
])
def test_set_after_restart(wfs_wms_status_before, wfs_wms_status_after):
    workspace = 'wfs_wms_status_test_workspace'
    publ_type = LAYER_TYPE
    publication_name = f'{publ_type.split(".")[1]}_{wfs_wms_status_before.value}'

    uuid_orig = uuid.uuid4()
    uuid_str = str(uuid_orig)
    db_info = {"name": publication_name,
               "title": publication_name,
               "publ_type_name": publ_type,
               "uuid": uuid_str,
               "access_rights": {'read': ['EVERYONE'], 'write': ['EVERYONE']},
               "actor_name": None,
               "geodata_type": 'vector',
               'style_type': 'sld' if publ_type == LAYER_TYPE else None,
               'image_mosaic': False,
               'external_table_uri': None,
               'wfs_wms_status': wfs_wms_status_before.value,
               }

    with app.app_context():
        pubs_util.insert_publication(workspace, db_info)

        set_after_restart()

    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, publication_name, {'keys': ['wfs_wms_status']})
    wfs_wms_status = publ_info['_wfs_wms_status']
    assert wfs_wms_status == wfs_wms_status_after

    with app.app_context():
        pubs_util.delete_publication(workspace_name=workspace,
                                     type=publ_type,
                                     name=publication_name,
                                     )
