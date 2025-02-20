import uuid
from layman import settings, app, util as layman_util
from layman.common.prime_db_schema import publications, workspaces, users

oauth2_sub_counter = layman_util.SimpleCounter()


def ensure_workspace(workspace):
    with app.app_context():
        return workspaces.ensure_workspace(workspace)


def ensure_user(workspace):
    workspace_id = ensure_workspace(workspace)
    oauth2_sub_counter.increase()
    user_info = {
        'sub': oauth2_sub_counter.get(),
        'issuer_id': 'layman',
        'claims': {
            'email': f"{workspace}@oauth2.org",
            'name': workspace,
            'middle_name': '',
            'family_name': workspace,
            'given_name': workspace,
            'preferred_username': workspace,
        }
    }
    with app.app_context():
        users.ensure_user(workspace_id, user_info)


def post_workspace_publication(publication_type, workspace, name, *, actor=None, access_rights=None, title=None,
                               bbox=None, crs=None, style_type='sld', geodata_type=None, wfs_wms_status=None,
                               publ_uuid=None):
    assert (bbox is None) == (crs is None), f'bbox={bbox}, crs={crs}'
    access_rights = access_rights or {}
    publ_uuid = publ_uuid or uuid.uuid4()
    default_access_rights = {settings.RIGHTS_EVERYONE_ROLE} if not actor else {actor}
    for right_type in ['read', 'write']:
        access_rights[right_type] = access_rights.get(right_type, default_access_rights)

    with app.app_context():
        publications.insert_publication(workspace, {
            'name': name,
            'title': title or name,
            'publ_type_name': publication_type,
            'uuid': publ_uuid,
            'actor_name': actor,
            'geodata_type': geodata_type,
            'style_type': style_type,
            'access_rights': access_rights,
            'image_mosaic': False,
            'wfs_wms_status': wfs_wms_status,
        })
        if bbox:
            publications.set_bbox(workspace, publication_type, name, bbox, crs)


def clear_workspace(workspace):
    with app.app_context():
        for _, publication_type, name in publications.get_publication_infos(workspace_name=workspace,
                                                                            ):
            publications.delete_publication(workspace, publication_type, name)


def clear_workspaces(workspaces):
    for workspace in workspaces:
        clear_workspace(workspace)
