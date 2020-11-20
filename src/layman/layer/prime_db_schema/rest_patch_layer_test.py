from layman import settings, app
from layman.common import geoserver
from test import process, process_client

ensure_layman = process.ensure_layman
liferay_mock = process.liferay_mock


def test_patch_gs_access_rights(liferay_mock):
    username = 'test_patch_gs_access_rights_user'
    layername = 'test_patch_gs_access_rights_layer'

    gs_username = 'USER_' + username.upper()
    gs_anonymous = 'ROLE_ANONYMOUS'

    authn_headers1 = process_client.get_authz_headers(username)
    headers1 = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
        **authn_headers1,
    }

    access_rights = {'read': f'{username}, {settings.RIGHTS_EVERYONE_ROLE}',
                     'write': f'{username}, {settings.RIGHTS_EVERYONE_ROLE}'}
    layman_process = process.start_layman(dict(**process.AUTHN_SETTINGS))

    process_client.reserve_username(username, headers=authn_headers1)
    process_client.publish_layer(username,
                                 layername,
                                 headers=authn_headers1,
                                 access_rights=access_rights
                                 )

    read_rule = geoserver.get_security_roles(f'{username}.{layername}.r', settings.LAYMAN_GS_AUTH)
    assert read_rule == {gs_username, gs_anonymous}
    write_rule = geoserver.get_security_roles(f'{username}.{layername}.w', settings.LAYMAN_GS_AUTH)
    assert write_rule == {gs_username, gs_anonymous}

    process_client.patch_layer(username,
                               layername,
                               headers=authn_headers1,
                               file_paths=['tmp/naturalearth/110m/cultural/ne_110m_admin_0_countries.geojson'])

    read_rule = geoserver.get_security_roles(f'{username}.{layername}.r', settings.LAYMAN_GS_AUTH)
    assert read_rule == {gs_username, gs_anonymous}
    write_rule = geoserver.get_security_roles(f'{username}.{layername}.w', settings.LAYMAN_GS_AUTH)
    assert write_rule == {gs_username, gs_anonymous}

    process_client.delete_layer(username, layername, headers1)

    process.stop_process(layman_process)
