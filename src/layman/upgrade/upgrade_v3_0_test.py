import pytest
from lxml import etree as ET

from layman import app, settings, common
from layman.common.micka import util as common_util, requests as micka_requests
from layman.map.map_class import Map
from layman.map.micka import csw as map_csw
from layman.upgrade import upgrade_v3_0
from test_tools import process_client
from test_tools import util as test_util


def update_metadata_values(publication, *, metadata_properties_to_refresh=None, actor_name=None,
                           timeout=None, **kwargs):
    timeout = timeout or settings.DEFAULT_CONNECTION_TIMEOUT
    metadata_properties_to_refresh = metadata_properties_to_refresh or []
    assert len(metadata_properties_to_refresh) > 0, "metadata_properties_to_refresh cannot be empty"

    csw = common_util.create_csw()
    assert publication.uuid is not None, "publication.uuid cannot be None"
    assert csw is not None, "csw cannot be None"

    muuid = publication.micka_ids.id
    element = common_util.get_record_element_by_id(csw, muuid)
    assert element is not None, f"metadata record with muuid {muuid} does not exist"

    _, prop_values = map_csw.get_template_path_and_values(
        publication, http_method=common.REQUEST_METHOD_PATCH, actor_name=actor_name
    )
    prop_values.update(kwargs)
    prop_values = {
        k: v for k, v in prop_values.items()
        if k in metadata_properties_to_refresh + ['md_date_stamp']
    }
    element = common_util.fill_xml_template_obj(element, prop_values, map_csw.METADATA_PROPERTIES)
    record = ET.tostring(element, encoding='unicode', pretty_print=True)

    micka_requests.csw_update({
        'muuid': muuid,
        'record': record,
    }, timeout=timeout)


@pytest.mark.usefixtures('ensure_layman')
def test_update_graphic_url_metadata():
    workspace = 'test_workspace'
    mapname = 'test_map'

    with app.app_context():
        process_client.ensure_workspace(workspace)
        map_uuid = 'af238200-8200-1a23-9399-42c9fca53543'
        process_client.publish_workspace_map(
            workspace=workspace,
            name=mapname,
            uuid=map_uuid
        )

    old_thumbnail_url = f"{settings.LAYMAN_SERVER_NAME}/rest/workspaces/{workspace}/maps/{mapname}/thumbnail"

    with app.app_context():
        publication = Map(map_tuple=(workspace, mapname))
        update_metadata_values(
            publication=publication,
            metadata_properties_to_refresh=['graphic_url'],
            actor_name=workspace,
            graphic_url=old_thumbnail_url
        )
        csw_info = map_csw.get_metadata_comparison(Map(map_tuple=(workspace, mapname)))

    csw_url = next(iter(csw_info.keys()))
    metadata = csw_info[csw_url]
    assert metadata['graphic_url'] == old_thumbnail_url, (
        f"graphic_url did not match: expected '{old_thumbnail_url}', got '{metadata['graphic_url']}'"
    )

    with app.app_context():
        upgrade_v3_0.migrate_graphic_urls()
        csw_info = map_csw.get_metadata_comparison(Map(map_tuple=(workspace, mapname)))

    csw_url = next(iter(csw_info.keys()))
    metadata = csw_info[csw_url]

    with app.app_context():
        new_thumbnail_url = test_util.url_for_external('rest_map_thumbnail.get', uuid=map_uuid)

    assert metadata['graphic_url'] == new_thumbnail_url, (
        f"graphic_url should be new format URL: expected '{new_thumbnail_url}', got '{metadata['graphic_url']}'"
    )

    with app.app_context():
        process_client.delete_workspace_map(workspace, mapname)
