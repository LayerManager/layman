import json

import tools.client
from tools.test_data import USERS, PUBLICATIONS, UUID_FILE_PATH
from tools.oauth2_provider_mock import OAuth2ProviderMock


def main():
    with OAuth2ProviderMock():
        client = tools.client.RestClient("http://localhost:8000")

        for username in USERS:
            print(f"Reserving username {username}")
            client.reserve_username(username, actor_name=username)

        publ_uuids = []
        for publ in PUBLICATIONS:
            print(f"Reserving publication {publ.type, publ.workspace, publ.name}")
            publ_resp = client.post_workspace_publication(publ.type, publ.workspace, publ.name, actor_name=publ.owner,
                                                          **publ.rest_args)
            publ_uuid = publ_resp['uuid']
            publ_uuids.append([publ.type, publ.workspace, publ.name, publ_uuid])

            publ_detail = client.get_workspace_publication(publ.type, publ.workspace, publ.name, actor_name=publ.owner)
            assert publ_detail['layman_metadata']['publication_status'] == 'COMPLETE', f'rest_publication_detail={publ_detail}'
            assert publ_detail['description'] == publ.rest_args['description'], f'rest_publication_detail={publ_detail}'

        with open(UUID_FILE_PATH, 'w', encoding='utf-8') as uuid_file:
            json.dump(publ_uuids, uuid_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
