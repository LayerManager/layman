import pytest

from geoserver.error import Error
from test_tools import process_client
from layman.layer.geoserver import GEOSERVER_WFS_WORKSPACE, GeoserverIds


@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
def test_issue_1081():
    workspace = 'dynamic_test_workspace_layer_issue_1081'
    layer1 = 'issue_1081_layer_1'
    layer1_uuid = '03440543-4b2a-4499-bebf-e2a632c25576'
    layer2 = 'issue_1081_layer_2'
    layer2_uuid = 'd7247e9f-8f86-4438-82da-3f53e48df95f'

    process_client.publish_workspace_layer(workspace=workspace,
                                           name=layer1,
                                           uuid=layer1_uuid,
                                           )
    process_client.publish_workspace_layer(workspace=workspace,
                                           name=layer2,
                                           uuid=layer2_uuid,
                                           )
    wfs_layer1 = GeoserverIds(uuid=layer1_uuid).wfs
    wfs_layer2 = GeoserverIds(uuid=layer2_uuid).wfs

    wfst_data = f'''<?xml version="1.0"?>
<wfs:Transaction version="2.0.0" service="WFS" xmlns:layman="http://layman" xmlns:fes="http://www.opengis.net/fes/2.0"
                 xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:wfs="http://www.opengis.net/wfs/2.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xsi:schemaLocation="http://www.opengis.net/wfs/2.0                       http://schemas.opengis.net/wfs/2.0/wfs.xsd                       http://www.opengis.net/gml/3.2                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
    <wfs:Update typeName="{wfs_layer2.workspace}:{wfs_layer2.name}">
        <wfs:Property>
            <wfs:ValueReference>{wfs_layer2.workspace}:new_layer2_attr_update</wfs:ValueReference>
            <wfs:Value>some value</wfs:Value>
        </wfs:Property>
    </wfs:Update>
    <wfs:Replace>
        <{wfs_layer1.workspace}:{wfs_layer1.name}>
            <{wfs_layer1.workspace}:wkb_geometry>
                <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                    <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
                </gml:Point>
            </{wfs_layer1.workspace}:wkb_geometry>
            <{wfs_layer1.workspace}:name>New name</{wfs_layer1.workspace}:name>
            <{wfs_layer1.workspace}:labelrank>3</{wfs_layer1.workspace}:labelrank>
            <{wfs_layer1.workspace}:new_layer1_attr_replace>some value</{wfs_layer1.workspace}:new_layer1_attr_replace>
        </{wfs_layer1.workspace}:{wfs_layer1.name}>
        <fes:Filter>
            <fes:ResourceId rid="{wfs_layer1.name}.1"/>
        </fes:Filter>
    </wfs:Replace>
</wfs:Transaction>'''

    with pytest.raises(Error):
        process_client.post_wfst(
            wfst_data,
        )

    with pytest.raises(Error):
        process_client.post_wfst(
            wfst_data,
            workspace=GEOSERVER_WFS_WORKSPACE,
        )

    process_client.delete_workspace_layers(workspace=workspace)
