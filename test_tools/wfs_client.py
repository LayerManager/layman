from enum import Enum

from layman import names, util, app
from layman.layer.geoserver import GeoserverNameForSource
from test_tools.data import wfs as data_wfs
from . import process_client


class WfstOperation(Enum):
    INSERT = 1


class WfstVersion(Enum):
    WFS20 = 1


WfstOperationDef = {
    (WfstOperation.INSERT, WfstVersion.WFS20): data_wfs.get_wfs20_insert_points,
}


def post_wfst(workspace, publ_type, name,
              *,
              operation: WfstOperation,
              version: WfstVersion,
              request_headers=None,
              request_url=None,
              request_workspace=None,
              wait_for_update=True,
              ):
    assert publ_type == process_client.LAYER_TYPE
    with app.app_context():
        uuid = util.get_publication_uuid(workspace=workspace, publ_type=publ_type, publ_name=name)

    wfs_layer = names.get_names_by_source(uuid=uuid, publication_type=publ_type).wfs or GeoserverNameForSource(workspace=workspace, name=name)
    data_xml = WfstOperationDef[(operation, version)](wfs_layer.workspace, wfs_layer.name)

    process_client.post_wfst(data_xml, headers=request_headers, url=request_url, workspace=request_workspace)

    if wait_for_update:
        process_client.wait_for_publication_status(workspace, publ_type, name, headers=request_headers)
