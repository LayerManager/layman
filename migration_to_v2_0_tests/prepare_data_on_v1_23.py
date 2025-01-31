import json

from db import util as db_util
import layman_settings as settings
import tools.client
from tools.test_data import USERS, PUBLICATIONS, INCOMPLETE_LAYERS, UUID_FILE_PATH
from tools.oauth2_provider_mock import OAuth2ProviderMock


DB_URI = f"postgresql://{settings.LAYMAN_PG_USER}:{settings.LAYMAN_PG_PASSWORD}@localhost:25433/{settings.LAYMAN_PG_DBNAME}"


def main():
    with OAuth2ProviderMock():
        client = tools.client.RestClient("http://localhost:8000")

        for username in USERS:
            print(f"Reserving username {username}")
            client.reserve_username(username, actor_name=username)

        publ_uuids = []
        for layer in PUBLICATIONS:
            print(f"Reserving publication {layer.type, layer.workspace, layer.name}")
            publ_resp = client.post_workspace_publication(layer.type, layer.workspace, layer.name, actor_name=layer.owner,
                                                          **layer.rest_args)
            publ_uuid = publ_resp['uuid']
            publ_uuids.append([layer.type, layer.workspace, layer.name, publ_uuid])

            publ_detail = client.get_workspace_publication(layer.type, layer.workspace, layer.name, actor_name=layer.owner)
            assert publ_detail['layman_metadata']['publication_status'] == 'COMPLETE', f'rest_publication_detail={publ_detail}'
            assert publ_detail['description'] == layer.rest_args['description'], f'rest_publication_detail={publ_detail}'

        with open(UUID_FILE_PATH, 'w', encoding='utf-8') as uuid_file:
            json.dump(publ_uuids, uuid_file, ensure_ascii=False, indent=4)

        for layer in INCOMPLETE_LAYERS:
            print(f"Set WFS_WMS_COMPLETE to incomplete for publication {layer.type, layer.workspace, layer.name}")
            assert layer.type == 'layman.layer'
            db_util.run_statement(f"update {settings.LAYMAN_PRIME_SCHEMA}.publications set wfs_wms_status = %s where uuid = %s",
                                     data=(settings.EnumWfsWmsStatus.NOT_AVAILABLE.value, layer.uuid,), uri_str=DB_URI)



if __name__ == "__main__":
    main()
