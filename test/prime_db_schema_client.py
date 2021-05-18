import uuid
from layman import settings, app
from layman.common.prime_db_schema import publications, workspaces, users

latest_oauth2_sub = 0  # pylint: disable=invalid-name


def ensure_workspace(workspace):
    with app.app_context():
        return workspaces.ensure_workspace(workspace)


def ensure_user(workspace):
    workspace_id = ensure_workspace(workspace)
    global latest_oauth2_sub  # pylint: disable=invalid-name
    latest_oauth2_sub += 1
    user_info = {
        'sub': latest_oauth2_sub,
        'issuer_id': 'layman',
        'claims': {
            'email': f"{workspace}@liferay.com",
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
                               bbox=None, style_type='sld'):
    access_rights = access_rights or {}
    default_access_rights = {settings.RIGHTS_EVERYONE_ROLE} if not actor else {actor}
    for right_type in ['read', 'write']:
        access_rights[right_type] = access_rights.get(right_type, default_access_rights)

    with app.app_context():
        publications.insert_publication(workspace, {
            'name': name,
            'title': title or name,
            'publ_type_name': publication_type,
            'uuid': uuid.uuid4(),
            'actor_name': actor,
            'style_type': style_type,
            'access_rights': access_rights,
        })
        if bbox:
            publications.set_bbox(workspace, publication_type, name, bbox)


def clear_workspace(workspace):
    with app.app_context():
        for _, publication_type, name in publications.get_publication_infos(workspace_name=workspace,
                                                                            ):
            publications.delete_publication(workspace, publication_type, name)


def clear_workspaces(workspaces):
    for workspace in workspaces:
        clear_workspace(workspace)
