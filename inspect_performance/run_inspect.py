import csv
import time
from dataclasses import dataclass

from performance_tools.client import LAYER_TYPE, RestClient
from performance_tools.oauth2_provider_mock import OAuth2ProviderMock
import layman_settings as settings

USER_1 = 'performance_user_1'
USER_2 = 'performance_user_2'
USER_3 = 'performance_user_3'

USERS = [
    USER_1,
    USER_2,
    USER_3,
]


@dataclass
class Publication:
    type: str
    workspace: str
    name: str
    rest_args: dict
    uuid = None


@dataclass
class WmsCapabilitiesRequest:
    actor_name: str
    exp_layer_prefixes: list


def main():
    n_cycles = 600
    csv_file_path = 'tmp/performance.csv'

    with ((OAuth2ProviderMock())):

        client = RestClient("http://localhost:8000")

        for username in USERS:
            print(f"Reserving username {username}")
            client.reserve_username(username, actor_name=username)

        all_publications = []

        for cycle_n in range(1, n_cycles + 1):
            print(f"Running cycle {cycle_n}/{n_cycles}")

            time_report = {'cycle': cycle_n}

            start_cycle = time.time()

            # define publications to post
            publications_to_post = [
                Publication(type=LAYER_TYPE,
                            workspace=USER_1,
                            name=f'private_layer_{cycle_n}',
                            rest_args={
                                'access_rights': {'read': USER_1},
                                'actor_name': USER_1,
                            },
                            ),
                Publication(type=LAYER_TYPE,
                            workspace=USER_2,
                            name=f'shared_layer_{cycle_n}',
                            rest_args={
                                'access_rights': {'read': f"{USER_2},{USER_3}"},
                                'actor_name': USER_2,
                            },
                            ),
                Publication(type=LAYER_TYPE,
                            workspace=USER_3,
                            name=f'public_layer_{cycle_n}',
                            rest_args={
                                'access_rights': {'read': 'EVERYONE'},
                                'actor_name': USER_3,
                            },
                            ),
            ]

            # post publications
            start_post_publs = time.time()
            for publ in publications_to_post:
                start_post_publ = time.time()
                resp_json = client.post_workspace_publication(publication_type=publ.type,
                                                              workspace=publ.workspace,
                                                              name=publ.name,
                                                              **publ.rest_args,
                                                              )
                publ.uuid = resp_json['uuid']
                all_publications.append(publ)
                layer_prefix = publ.name.rsplit('_', 1)[0]
                time_report[f"post_{layer_prefix}"] = time.time() - start_post_publ
            time_report['post_all_layers'] = time.time() - start_post_publs

            # define wms capabilities requests
            wms_requests = [
                WmsCapabilitiesRequest(actor_name=USER_1, exp_layer_prefixes=['private_layer', 'public_layer']),
                WmsCapabilitiesRequest(actor_name=USER_2, exp_layer_prefixes=['shared_layer', 'public_layer']),
                WmsCapabilitiesRequest(actor_name=USER_3, exp_layer_prefixes=['shared_layer', 'public_layer']),
                WmsCapabilitiesRequest(actor_name=settings.ANONYM_USER, exp_layer_prefixes=['public_layer']),
            ]

            # send wms capabilities requests
            start_wms_requests = time.time()
            for wms_request in wms_requests:
                start_wms_request = time.time()
                wms_cap = client.get_wms_capabilities(geoserver_workspace='layman_wms',
                                                      actor_name=wms_request.actor_name)

                # assert publi
                assert len(wms_cap.contents) == len(wms_request.exp_layer_prefixes) * cycle_n, (
                    f"len(wms_cap.contents)={len(wms_cap.contents)}\n"
                    f"len(wms_request.exp_publ_prefixes)={len(wms_request.exp_layer_prefixes)}\n"
                    f"cycle_n={cycle_n}\n"
                    f"wms_cap.contents.keys()={wms_cap.contents.keys()}\n")
                exp_layer_names = {
                    f"l_{publ.uuid}"
                    for publ in all_publications
                    if any(prefix in publ.name for prefix in wms_request.exp_layer_prefixes)
                }
                assert set(exp_layer_names) == set(wms_cap.contents.keys()), set(exp_layer_names).symmetric_difference(set(wms_cap.contents.keys()))
                time_report[f"get_wms_{wms_request.actor_name}"] = time.time() - start_wms_request
            time_report['get_all_wms'] = time.time() - start_wms_requests

            time_report['all_cycle'] = time.time() - start_cycle

            # write time report
            print(time_report)
            if cycle_n == 1:
                with open(csv_file_path, "w", newline='', encoding='utf-8') as csv_file:
                    csv_writer = csv.DictWriter(csv_file, fieldnames=time_report.keys())
                    csv_writer.writeheader()
                    csv_writer.writerow(time_report)
            else:
                with open(csv_file_path, "a", newline='', encoding='utf-8') as csv_file:
                    csv_writer = csv.DictWriter(csv_file, fieldnames=time_report.keys())
                    csv_writer.writerow(time_report)


if __name__ == "__main__":
    main()
