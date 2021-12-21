from enum import Enum

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
              ):
    assert publ_type == process_client.LAYER_TYPE

    data_xml = WfstOperationDef[(operation, version)](workspace, name)

    process_client.post_wfst(data_xml, headers=request_headers, url=request_url, workspace=request_workspace)
