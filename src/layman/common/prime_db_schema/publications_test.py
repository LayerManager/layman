import uuid
import pytest

import crs as crs_def
from layman import settings, app as app, LaymanError
from layman.layer import LAYER_TYPE
from layman.map import MAP_TYPE
from test_tools import process_client, prime_db_schema_client
from . import publications, workspaces, users

DB_SCHEMA = settings.LAYMAN_PRIME_SCHEMA

userinfo_baseline = {"issuer_id": 'mock_test_publications_test',
                     "claims": {"email": "test@liferay.com",
                                "preferred_username": 'test_preferred',
                                "name": "test ensure user",
                                "given_name": "test",
                                "family_name": "user",
                                "middle_name": "ensure",
                                }
                     }


def test_publication_basic():
    def publications_by_type(prefix,
                             publication_type,
                             style_type,
                             ):
        username = prefix + '_username'
        publication_name = prefix + '_pub_name'
        publication_title = prefix + '_pub_ Title'
        publication_title2 = prefix + '_pub_ Title2'

        with app.app_context():
            workspaces.ensure_workspace(username)
            uuid_orig = uuid.uuid4()
            uuid_str = str(uuid_orig)
            db_info = {"name": publication_name,
                       "title": publication_title,
                       "publ_type_name": publication_type,
                       "uuid": uuid_orig,
                       "actor_name": username,
                       'style_type': style_type,
                       "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                         "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                         },
                       }
            publications.insert_publication(username, db_info)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs[(username, publication_type, publication_name)].get('name') == publication_name
            assert pubs[(username, publication_type, publication_name)].get('title') == publication_title
            assert pubs[(username, publication_type, publication_name)].get('uuid') == str(uuid_str)

            publ_info = pubs[(username, publication_type, publication_name)]
            assert 'file_type' in publ_info
            assert publ_info['file_type'] is None

            db_info = {"name": publication_name,
                       "title": publication_title2,
                       "actor_name": username,
                       "publ_type_name": publication_type,
                       "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                         "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                         },
                       'style_type': style_type,
                       }
            publications.update_publication(username, db_info)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs[(username, publication_type, publication_name)].get('name') == publication_name
            assert pubs[(username, publication_type, publication_name)].get('title') == publication_title2
            assert pubs[(username, publication_type, publication_name)].get('uuid') == uuid_str

            db_info = {"name": publication_name,
                       "title": publication_title,
                       "actor_name": username,
                       "publ_type_name": publication_type,
                       "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                         "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                         },
                       'style_type': style_type,
                       }
            publications.update_publication(username, db_info)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs[(username, publication_type, publication_name)].get('name') == publication_name
            assert pubs[(username, publication_type, publication_name)].get('title') == publication_title
            assert pubs[(username, publication_type, publication_name)].get('uuid') == uuid_str

            publications.delete_publication(username, publication_type, publication_name)
            pubs = publications.get_publication_infos(username, publication_type)
            assert pubs.get((username, publication_type, publication_name)) is None

            workspaces.delete_workspace(username)

    publications_by_type('test_publication_basic_layer',
                         LAYER_TYPE,
                         'sld',
                         )
    publications_by_type('test_publication_basic_map',
                         MAP_TYPE,
                         None,
                         )


class TestSelectPublicationsBasic:
    workspace1 = 'test_select_publications_basic_workspace1'
    workspace2 = 'test_select_publications_basic_workspace2'
    qml_style_file = 'sample/style/small_layer.qml'
    publications = [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le', dict()),
                    (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml', {'style_file': qml_style_file}),
                    (workspace1, MAP_TYPE, 'test_select_publications_publication1me', dict()),
                    (workspace2, LAYER_TYPE, 'test_select_publications_publication2le', dict()),
                    ]

    @pytest.fixture(scope="class")
    def provide_data(self):
        for publication in self.publications:
            process_client.publish_workspace_publication(publication[1], publication[0], publication[2], **publication[3])
        yield
        for publication in self.publications:
            process_client.delete_workspace_publication(publication[1], publication[0], publication[2])

    @staticmethod
    @pytest.mark.parametrize('query_params, expected_publications', [
        ({'workspace_name': workspace1, 'pub_type': LAYER_TYPE},
         [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'),
          (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'),
          ]),
        ({'workspace_name': workspace1, 'pub_type': MAP_TYPE}, [(workspace1, MAP_TYPE, 'test_select_publications_publication1me'), ]),
        ({'workspace_name': workspace1, 'style_type': 'qml'},
         [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'), ]),
        ({'workspace_name': workspace1, 'style_type': 'sld'},
         [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'), ]),
        ({'workspace_name': workspace1}, [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'),
                                          (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'),
                                          (workspace1, MAP_TYPE, 'test_select_publications_publication1me'),
                                          ]),
        (dict(), [(workspace1, LAYER_TYPE, 'test_select_publications_publication1le'),
                  (workspace1, LAYER_TYPE, 'test_select_publications_publication1le_qml'),
                  (workspace1, MAP_TYPE, 'test_select_publications_publication1me'),
                  (workspace2, LAYER_TYPE, 'test_select_publications_publication2le'),
                  ]),
    ])
    @pytest.mark.usefixtures('ensure_layman', 'provide_data')
    def test_get_publications(query_params, expected_publications):
        with app.app_context():
            infos = publications.get_publication_infos(**query_params)
        info_publications = list(infos.keys())
        assert expected_publications == info_publications


class TestSelectPublicationsComplex:
    workspace1 = 'test_select_publications_complex_workspace1'
    workspace2 = 'test_select_publications_complex_workspace2'
    workspace3 = 'test_select_publications_complex_workspace3'

    map_1e_2_4x6_6 = 'test_select_publications_map1e'
    map_1e_3_3x3_3 = 'test_select_publications_map1e_3_3x3_3'
    map_1o_2_2x3_6 = 'test_select_publications_map1o'
    map_1oe_3_7x5_9 = 'test_select_publications_map1oe'
    map_2e_3_3x5_5 = 'test_select_publications_map2e'
    map_2o_2_2x4_4 = 'test_select_publications_map2o'
    map_3o_null = 'test_select_publications_map3o'

    # Name of the publications consists of <publication_type>-<workspace_number><visibility(E=everyone, O=owner)>-<extent in EPSG:3857>
    # extent is in thousands with (1840000, 6320000, 1840000, 6320000) as a baseline
    publications = [
        (workspace1, MAP_TYPE, map_1e_2_4x6_6,
         {'title': 'Příliš žluťoučký Kůň úpěl ďábelské ódy',
          'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                            'write': {settings.RIGHTS_EVERYONE_ROLE}},
          'bbox': (1842000, 6324000, 1846000, 6326000),
          'crs': crs_def.EPSG_3857,
          }),
        (workspace1, MAP_TYPE, map_1e_3_3x3_3,
         {'title': 'Jednobodová vrstva Kodaň',
          'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                            'write': {settings.RIGHTS_EVERYONE_ROLE}},
          'bbox': (16.55595068632278, 49.28289621550056, 16.55595068632278, 49.28289621550056),
          'crs': crs_def.EPSG_4326,
          }),
        (workspace1, MAP_TYPE, map_1o_2_2x3_6,
         {'title': 'Ďůlek kun Karel',
          'access_rights': {'read': {workspace1},
                            'write': {workspace1}},
          'bbox': (-601597.1407428421, -1151286.9441679057, -600665.4471820187, -1148625.2345234894),
          'crs': crs_def.EPSG_5514,
          }),
        (workspace1, MAP_TYPE, map_1oe_3_7x5_9,
         {'title': 'jedna dva tři čtyři kód',
          'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                            'write': {workspace1}},
          'bbox': (613077.7082822081, 5462674.538979379, 614410.4777841105, 5464003.656058598),
          'crs': crs_def.EPSG_32633,
          }),
        (workspace2, MAP_TYPE, map_2e_3_3x5_5,
         {'title': 'Svíčky is the best game',
          'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                            'write': {settings.RIGHTS_EVERYONE_ROLE}},
          'bbox': (176844.09626803786, 5468335.761457844, 178226.55642100016, 5469714.707582928),
          'crs': crs_def.EPSG_32634,
          }),
        (workspace2, MAP_TYPE, map_2o_2_2x4_4,
         {'title': 'druhá mapa JeDnA óda',
          'access_rights': {'read': {workspace2},
                            'write': {workspace2}},
          'bbox': (4459469.209282893, 2527850.676486253, 4460838.491401795, 2529216.681901061),
          'crs': crs_def.EPSG_3034,
          }),
        (workspace3, MAP_TYPE, map_3o_null,
         {'title': 'Nullový bounding box',
          'access_rights': {'read': {workspace3},
                            'write': {workspace3}},
          'bbox': (None, None, None, None),
          'crs': crs_def.EPSG_3035,
          }),
    ]

    @pytest.fixture(scope="class")
    def provide_data(self):
        workspaces = [self.workspace1, self.workspace2, self.workspace3]
        for workspace in workspaces:
            prime_db_schema_client.ensure_user(workspace)
        for workspace, publ_type, publ_name, publ_params in self.publications:
            prime_db_schema_client.post_workspace_publication(publ_type, workspace, publ_name, actor=workspace,
                                                              **publ_params)
        yield
        prime_db_schema_client.clear_workspaces(workspaces)

    @staticmethod
    @pytest.mark.parametrize('query_params, expected_result', [
        (dict(), {
            'items': [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      (workspace3, MAP_TYPE, map_3o_null),
                      ],
            'total_count': 7,
            'content_range': (1, 7),
        }),
        ({'reader': settings.ANONYM_USER}, {
            'items': [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      ],
            'total_count': 4,
            'content_range': (1, 4),
        }),
        ({'reader': workspace2}, {
            'items': [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      ],
            'total_count': 5,
            'content_range': (1, 5),
        }),
        ({'writer': settings.ANONYM_USER}, {
            'items': [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      ],
            'total_count': 3,
            'content_range': (1, 3),
        }),
        ({'writer': workspace2}, {
            'items': [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      ],
            'total_count': 4,
            'content_range': (1, 4),
        }),
        ({'full_text_filter': 'dva'}, {
            'items': [(workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      ],
            'total_count': 1,
            'content_range': (1, 1),
        }),
        ({'full_text_filter': 'games'}, {
            'items': [(workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      ],
            'total_count': 1,
            'content_range': (1, 1),
        }),
        ({'full_text_filter': 'kun'}, {
            'items': [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      ],
            'total_count': 2,
            'content_range': (1, 2),
        }),
        ({'full_text_filter': 'jedna'}, {
            'items': [(workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      ],
            'total_count': 2,
            'content_range': (1, 2),
        }),
        ({'full_text_filter': 'upet'}, {
            'items': [],
            'total_count': 0,
            'content_range': (0, 0),
        }),
        ({'full_text_filter': 'dva kun'}, {
            'items': [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      ],
            'total_count': 3,
            'content_range': (1, 3),
        }),
        ({'full_text_filter': 'dn'}, {
            'items': [(workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      ],
            'total_count': 3,
            'content_range': (1, 3),
        }),
        ({'full_text_filter': 'oda', 'ordering_full_text': 'oda', 'order_by_list': ['full_text'], }, {
            'items': [(workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      ],
            'total_count': 2,
            'content_range': (1, 2),
        }),
        ({'full_text_filter': 'va kód', 'ordering_full_text': 'va kód', 'order_by_list': ['full_text'], }, {
            'items': [(workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      ],
            'total_count': 2,
            'content_range': (1, 2),
        }),
        ({'order_by_list': ['full_text'], 'ordering_full_text': 'jedna'}, {
            'items': [(workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace3, MAP_TYPE, map_3o_null),
                      ],
            'total_count': 7,
            'content_range': (1, 7),
        }),
        ({'full_text_filter': 'dva kun', 'order_by_list': ['full_text'], 'ordering_full_text': 'karel kun'}, {
            'items': [(workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      ],
            'total_count': 3,
            'content_range': (1, 3),
        }),
        ({'order_by_list': ['title'], }, {
            'items': [(workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace3, MAP_TYPE, map_3o_null),
                      (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      ],
            'total_count': 7,
            'content_range': (1, 7),
        }),
        ({'order_by_list': ['last_change'], }, {
            'items': [(workspace3, MAP_TYPE, map_3o_null),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      ],
            'total_count': 7,
            'content_range': (1, 7),
        }),
        ({'order_by_list': ['bbox'],
          'ordering_bbox': (1842999, 6322999, 1845001, 6325001),
          'ordering_bbox_crs': crs_def.EPSG_3857,
          }, {
            'items': [(workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace3, MAP_TYPE, map_3o_null),
                      ],
            'total_count': 7,
            'content_range': (1, 7),
        }),
        ({'order_by_list': ['bbox'],
          'ordering_bbox': (16.5559417, 49.2828904, 16.573926, 49.2946205),  # EPSG:3857 (1842999, 6322999, 1845001, 6325001)
          'ordering_bbox_crs': crs_def.EPSG_4326,
          }, {
            'items': [(workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace3, MAP_TYPE, map_3o_null),
                      ],
            'total_count': 7,
            'content_range': (1, 7),
        }),
        ({'order_by_list': ['bbox'],
          'ordering_bbox': (-600879.43, -1150642.64, -599437.98, -1149487.13),  # EPSG:3857 (1842999, 6322999, 1845001, 6325001)
          'ordering_bbox_crs': crs_def.EPSG_5514,
          }, {
            'items': [(workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      (workspace3, MAP_TYPE, map_3o_null),
                      ],
            'total_count': 7,
            'content_range': (1, 7),
        }),
        ({'order_by_list': ['bbox'],
          'ordering_bbox': (1844001, 6324001, 1844001, 6324001),
          'ordering_bbox_crs': crs_def.EPSG_3857,
          'bbox_filter': (1844001, 6324001, 1844001, 6324001),
          'bbox_filter_crs': crs_def.EPSG_3857,
          }, {
            'items': [(workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      ],
            'total_count': 3,
            'content_range': (1, 3),
        }),
        ({'bbox_filter': (-600665, -1150641, -599439, -1149488),  # EPSG:3857 (1843001, 6323001, 1844999, 6324999)
          'bbox_filter_crs': crs_def.EPSG_5514,
          }, {
            'items': [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      ],
            'total_count': 3,
            'content_range': (1, 3),
        }),
        ({'bbox_filter': (176844.09626803786, 5468335.761457844, 176844.09626803786, 5468335.7614578441),  # EPSG:3857 (1843001, 6323001, 1843001, 6323001)
          'bbox_filter_crs': crs_def.EPSG_32634,
          }, {
            'items': [(workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      ],
            'total_count': 3,
            'content_range': (1, 3),
        }),
        ({'limit': 2}, {
            'items': [(workspace1, MAP_TYPE, map_1e_2_4x6_6),
                      (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                      # (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                      # (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                      # (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                      # (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                      # (workspace3, MAP_TYPE, map_3o_null),
                      ],
            'total_count': 7,
            'content_range': (1, 2),
        }),
        ({'offset': 2}, {
            'items': [
                # (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                # (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                (workspace3, MAP_TYPE, map_3o_null),
            ],
            'total_count': 7,
            'content_range': (3, 7),
        }),
        ({'limit': 5, 'offset': 5}, {
            'items': [
                # (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                # (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                # (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                # (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                # (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                (workspace3, MAP_TYPE, map_3o_null),
            ],
            'total_count': 7,
            'content_range': (6, 7),
        }),
        ({'limit': 2, 'offset': 2}, {
            'items': [
                # (workspace1, MAP_TYPE, map_1e_2_4x6_6),
                # (workspace1, MAP_TYPE, map_1e_3_3x3_3),
                (workspace1, MAP_TYPE, map_1o_2_2x3_6),
                (workspace1, MAP_TYPE, map_1oe_3_7x5_9),
                # (workspace2, MAP_TYPE, map_2e_3_3x5_5),
                # (workspace2, MAP_TYPE, map_2o_2_2x4_4),
                # (workspace3, MAP_TYPE, map_3o_null),
            ],
            'total_count': 7,
            'content_range': (3, 4),
        }),
        ({'limit': 0, 'offset': 0}, {
            'items': [
            ],
            'total_count': 7,
            'content_range': (0, 0),
        }),
    ])
    @pytest.mark.usefixtures('provide_data')
    def test_get_publication_infos_with_metainfo(query_params, expected_result):
        with app.app_context():
            infos = publications.get_publication_infos_with_metainfo(**query_params)
        info_publications = list(infos['items'].keys())
        assert set(expected_result['items']) == set(info_publications)
        assert expected_result['items'] == info_publications
        assert expected_result['total_count'] == infos['total_count']
        assert expected_result['content_range'] == infos['content_range']


class TestWorldBboxFilter:
    workspace = 'test_world_bbox_filter_workspace'
    layer_prefix = 'test_world_bbox_filter_layer'

    @pytest.fixture(scope="class")
    def provide_data(self):
        for crs, values in crs_def.CRSDefinitions.items():
            layer = self.layer_prefix + '_' + crs.split(':')[1]
            prime_db_schema_client.post_workspace_publication(LAYER_TYPE, self.workspace, layer)
            bbox = values.max_bbox or values.default_bbox
            with app.app_context():
                publications.set_bbox(self.workspace, LAYER_TYPE, layer, bbox, crs)
        yield
        prime_db_schema_client.clear_workspace(self.workspace)

    @staticmethod
    @pytest.mark.parametrize('crs', crs_def.CRSDefinitions.keys())
    @pytest.mark.usefixtures('provide_data')
    def test_world_bbox_filter(crs):
        with app.app_context():
            publications.get_publication_infos_with_metainfo(bbox_filter=(-100, -100, 100, 100),
                                                             bbox_filter_crs=crs)


def test_only_valid_names():
    workspace_name = 'test_only_valid_names_workspace'
    username = 'test_only_valid_names_user'

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '10'
        users.ensure_user(id_workspace_user, userinfo)

        publications.only_valid_names(set())
        publications.only_valid_names({username, })
        publications.only_valid_names({settings.RIGHTS_EVERYONE_ROLE, })
        publications.only_valid_names({settings.RIGHTS_EVERYONE_ROLE, username, })
        publications.only_valid_names({username, settings.RIGHTS_EVERYONE_ROLE, })

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({username, workspace_name})
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({workspace_name, username})
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({workspace_name, settings.RIGHTS_EVERYONE_ROLE, })
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            publications.only_valid_names({settings.RIGHTS_EVERYONE_ROLE, 'skaljgdalskfglshfgd', })
        assert exc_info.value.code == 43

        users.delete_user(username)
        workspaces.delete_workspace(workspace_name)


def test_at_least_one_can_write():
    workspace_name = 'test_at_least_one_can_write_workspace'
    username = 'test_at_least_one_can_write_user'

    publications.at_least_one_can_write({username, })
    publications.at_least_one_can_write({settings.RIGHTS_EVERYONE_ROLE, })
    publications.at_least_one_can_write({username, settings.RIGHTS_EVERYONE_ROLE, })
    publications.at_least_one_can_write({workspace_name, })
    publications.at_least_one_can_write({'lusfjdiaurghalskug', })

    with pytest.raises(LaymanError) as exc_info:
        publications.at_least_one_can_write(set())
    assert exc_info.value.code == 43


def test_who_can_write_can_read():
    workspace_name = 'test_who_can_write_can_read_workspace'
    username = 'test_who_can_write_can_read_user'

    publications.who_can_write_can_read(set(), set())
    publications.who_can_write_can_read({username, }, {username, })
    publications.who_can_write_can_read({username, workspace_name}, {username, })
    publications.who_can_write_can_read({username, settings.RIGHTS_EVERYONE_ROLE}, {username, })
    publications.who_can_write_can_read({username, settings.RIGHTS_EVERYONE_ROLE}, {username, settings.RIGHTS_EVERYONE_ROLE, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, }, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, }, {settings.RIGHTS_EVERYONE_ROLE, username, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, }, {settings.RIGHTS_EVERYONE_ROLE, workspace_name, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, username, }, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.who_can_write_can_read({settings.RIGHTS_EVERYONE_ROLE, username, }, set())
    publications.who_can_write_can_read({workspace_name, }, {workspace_name, })

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(set(), {workspace_name, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(set(), {username, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(set(), {settings.RIGHTS_EVERYONE_ROLE, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(username, {settings.RIGHTS_EVERYONE_ROLE, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.who_can_write_can_read(username, {workspace_name, })
    assert exc_info.value.code == 43


def test_i_can_still_write():
    workspace_name = 'test_i_can_still_write_workspace'
    username = 'test_who_can_write_can_read_user'

    publications.i_can_still_write(None, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(None, {username, settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(username, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(username, {workspace_name, settings.RIGHTS_EVERYONE_ROLE, })
    publications.i_can_still_write(username, {workspace_name, username, })

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(None, set())
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(None, {workspace_name, })
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(username, set())
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.i_can_still_write(username, {workspace_name, })
    assert exc_info.value.code == 43


def test_owner_can_still_write():
    workspace_name = 'test_owner_can_still_write_workspace'
    username = 'test_owner_can_still_write_user'

    publications.owner_can_still_write(None, set())
    publications.owner_can_still_write(None, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.owner_can_still_write(None, {username, })
    publications.owner_can_still_write(username, {settings.RIGHTS_EVERYONE_ROLE, })
    publications.owner_can_still_write(username, {username, })
    publications.owner_can_still_write(username, {username, workspace_name, })

    with pytest.raises(LaymanError) as exc_info:
        publications.owner_can_still_write(username, set())
    assert exc_info.value.code == 43

    with pytest.raises(LaymanError) as exc_info:
        publications.owner_can_still_write(username, {workspace_name, })
    assert exc_info.value.code == 43


def test_clear_roles():
    workspace_name = 'test_clear_roles_workspace'
    username = 'test_clear_roles_user'

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '20'
        users.ensure_user(id_workspace_user, userinfo)

        list = publications.clear_roles({username, }, workspace_name)
        assert list == {username, }, list

        list = publications.clear_roles({username, workspace_name, }, workspace_name)
        assert list == {username, workspace_name, }, list

        list = publications.clear_roles({username, }, username)
        assert list == set(), list

        list = publications.clear_roles({username, workspace_name, }, username)
        assert list == {workspace_name, }, list

        list = publications.clear_roles({username, settings.RIGHTS_EVERYONE_ROLE, }, workspace_name)
        assert list == {username, }, list

        list = publications.clear_roles({username, settings.RIGHTS_EVERYONE_ROLE, }, username)
        assert list == set(), list

        users.delete_user(username)
        workspaces.delete_workspace(workspace_name)


def assert_access_rights(workspace_name,
                         publication_name,
                         publication_type,
                         read_to_test,
                         write_to_test):
    pubs = publications.get_publication_infos(workspace_name, publication_type)
    assert pubs[(workspace_name, publication_type, publication_name)]["access_rights"]["read"] == read_to_test
    assert pubs[(workspace_name, publication_type, publication_name)]["access_rights"]["write"] == write_to_test


def test_insert_rights():
    def case_test_insert_rights(username,
                                publication_info_original,
                                access_rights,
                                read_to_test,
                                write_to_test,
                                ):
        publication_info = publication_info_original.copy()
        publication_info.update({"access_rights": access_rights})
        if users.get_user_infos(username):
            publication_info.update({"actor_name": username})
        publications.insert_publication(username, publication_info)
        assert_access_rights(username,
                             publication_info_original["name"],
                             publication_info_original["publ_type_name"],
                             read_to_test,
                             write_to_test,
                             )
        publications.delete_publication(username, publication_info["publ_type_name"], publication_info["name"])

    workspace_name = 'test_insert_rights_workspace'
    username = 'test_insert_rights_user'
    username2 = 'test_insert_rights_user2'

    publication_name = 'test_insert_rights_publication_name'
    publication_type = MAP_TYPE

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '30'
        users.ensure_user(id_workspace_user, userinfo)
        id_workspace_user2 = workspaces.ensure_workspace(username2)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '40'
        users.ensure_user(id_workspace_user2, userinfo)

        publication_info = {"name": publication_name,
                            "title": publication_name,
                            "actor_name": username,
                            "publ_type_name": publication_type,
                            "uuid": uuid.uuid4(),
                            }

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {username, },
                                 "write": {username, },
                                 },
                                [username, ],
                                [username, ],
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                 },
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 },
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_insert_rights(username,
                                publication_info,
                                {"read": {username, username2, },
                                 "write": {username, username2, },
                                 },
                                [username, username2, ],
                                [username, username2, ],
                                )

        case_test_insert_rights(workspace_name,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, username, },
                                 },
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_insert_rights(workspace_name,
                                publication_info,
                                {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                 },
                                [settings.RIGHTS_EVERYONE_ROLE, ],
                                [settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        users.delete_user(username)
        users.delete_user(username2)
        workspaces.delete_workspace(workspace_name)


def test_update_rights():
    def case_test_update_rights(username,
                                publication_info_original,
                                publication_update_info,
                                read_to_test,
                                write_to_test,
                                ):
        if not publication_update_info.get("publ_type_name"):
            publication_update_info["publ_type_name"] = publication_info_original["publ_type_name"]
        if not publication_update_info.get("name"):
            publication_update_info["name"] = publication_info_original["name"]
        publications.update_publication(username,
                                        publication_update_info,
                                        )
        assert_access_rights(username,
                             publication_info_original["name"],
                             publication_info_original["publ_type_name"],
                             read_to_test,
                             write_to_test,
                             )

    workspace_name = 'test_update_rights_workspace'
    username = 'test_update_rights_user'
    username2 = 'test_update_rights_user2'

    publication_name = 'test_update_rights_publication_name'
    publication_type = MAP_TYPE
    publication_insert_info = {"name": publication_name,
                               "title": publication_name,
                               "publ_type_name": publication_type,
                               "actor_name": username,
                               "uuid": uuid.uuid4(),
                               "access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                 "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                 },
                               }

    with app.app_context():
        workspaces.ensure_workspace(workspace_name)
        id_workspace_user = workspaces.ensure_workspace(username)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '50'
        users.ensure_user(id_workspace_user, userinfo)
        id_workspace_user2 = workspaces.ensure_workspace(username2)
        userinfo = userinfo_baseline.copy()
        userinfo['sub'] = '60'
        users.ensure_user(id_workspace_user2, userinfo)

        publications.insert_publication(username, publication_insert_info)

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': username},
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, username2, },
                                                   "write": {username, username2, },
                                                   },
                                 'actor_name': username},
                                [username, username2, ],
                                [username, username2, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': username},
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, },
                                                   "write": {username, },
                                                   },
                                 'actor_name': username},
                                [username, ],
                                [username, ],
                                )

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   "write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                   },
                                 'actor_name': None},
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                [username, settings.RIGHTS_EVERYONE_ROLE, ],
                                )

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username2, },
                                                       "write": {username2, },
                                                       },
                                     'actor_name': username2},
                                    [username, username2, ],
                                    [username, username2, ],
                                    )
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [username, username2, ],
                                    )
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"read": {username, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [username, username2, ],
                                    )
        assert exc_info.value.code == 43

        case_test_update_rights(username,
                                publication_insert_info,
                                {"access_rights": {"read": {username, },
                                                   "write": {username, },
                                                   },
                                 'actor_name': username},
                                [username, ],
                                [username, ],
                                )
        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"write": {username, username2, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [username, username2, username2, ],
                                    )
        assert exc_info.value.code == 43

        with pytest.raises(LaymanError) as exc_info:
            case_test_update_rights(username,
                                    publication_insert_info,
                                    {"access_rights": {"write": {settings.RIGHTS_EVERYONE_ROLE, },
                                                       },
                                     'actor_name': username},
                                    [username, username2, ],
                                    [settings.RIGHTS_EVERYONE_ROLE, ],
                                    )
        assert exc_info.value.code == 43

        publications.delete_publication(username, publication_insert_info["publ_type_name"], publication_insert_info["name"])
        users.delete_user(username)
        users.delete_user(username2)
        workspaces.delete_workspace(workspace_name)
