from enum import Enum, unique
import os
import pytest

import crs as crs_def
from layman import app, settings
from layman.common.prime_db_schema import publications as prime_db_schema_publications
from tests import EnumTestTypes, Publication
from tests.dynamic_data import base_test
from test_tools import process_client, prime_db_schema_client


@unique
class Key(Enum):
    REST_ARGS = 'rest_args'


DIRECTORY = os.path.dirname(os.path.abspath(__file__))
pytest_generate_tests = base_test.pytest_generate_tests

WORKSPACE1 = 'test_select_publications_complex_workspace1'
WORKSPACE2 = 'test_select_publications_complex_workspace2'
WORKSPACE3 = 'test_select_publications_complex_workspace3'
WORKSPACES = [WORKSPACE1, WORKSPACE2, WORKSPACE3]

MAP_1E_2_4X6_6 = Publication(WORKSPACE1, process_client.MAP_TYPE, 'test_select_publications_map1e')
MAP_1E_3_3X3_3 = Publication(WORKSPACE1, process_client.MAP_TYPE, 'test_select_publications_map1e_3_3x3_3')
MAP_1O_2_2X3_6 = Publication(WORKSPACE1, process_client.MAP_TYPE, 'test_select_publications_map1o')
MAP_1OE_3_7X5_9 = Publication(WORKSPACE1, process_client.MAP_TYPE, 'test_select_publications_map1oe')
MAP_2E_3_3X5_5 = Publication(WORKSPACE2, process_client.MAP_TYPE, 'test_select_publications_map2e')
MAP_2O_2_2X4_4 = Publication(WORKSPACE2, process_client.MAP_TYPE, 'test_select_publications_map2o')
MAP_3O_NULL = Publication(WORKSPACE3, process_client.MAP_TYPE, 'test_select_publications_map3o')

PUBLICATIONS = {
    MAP_1E_2_4X6_6: {
        'title': 'Příliš žluťoučký Kůň úpěl ďábelské ódy',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {settings.RIGHTS_EVERYONE_ROLE}},
        'bbox': (1842000, 6324000, 1846000, 6326000),
        'crs': crs_def.EPSG_3857,
    },
    MAP_1E_3_3X3_3: {
        'title': 'Jednobodová vrstva Kodaň',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {settings.RIGHTS_EVERYONE_ROLE}},
        'bbox': (16.55595068632278, 49.28289621550056, 16.55595068632278, 49.28289621550056),
        'crs': crs_def.EPSG_4326,
    },
    MAP_1O_2_2X3_6: {
        'title': 'Ďůlek kun Karel',
        'access_rights': {'read': {WORKSPACE1},
                          'write': {WORKSPACE1}},
        'bbox': (-601597.1407428421, -1151286.9441679057, -600665.4471820187, -1148625.2345234894),
        'crs': crs_def.EPSG_5514,
    },
    MAP_1OE_3_7X5_9: {
        'title': 'jedna dva tři čtyři kód',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {WORKSPACE1}},
        'bbox': (613077.7082822081, 5462674.538979379, 614410.4777841105, 5464003.656058598),
        'crs': crs_def.EPSG_32633,
    },
    MAP_2E_3_3X5_5: {
        'title': 'Svíčky is the best game',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {settings.RIGHTS_EVERYONE_ROLE}},
        'bbox': (176844.09626803786, 5468335.761457844, 178226.55642100016, 5469714.707582928),
        'crs': crs_def.EPSG_32634,
    },
    MAP_2O_2_2X4_4: {
        'title': 'druhá mapa JeDnA óda',
        'access_rights': {'read': {WORKSPACE2},
                          'write': {WORKSPACE2}},
        'bbox': (4459469.209282893, 2527850.676486253, 4460838.491401795, 2529216.681901061),
        'crs': crs_def.EPSG_3034,
    },
    MAP_3O_NULL: {
        'title': 'Nullový bounding box',
        'access_rights': {'read': {WORKSPACE3},
                          'write': {WORKSPACE3}},
        'bbox': (None, None, None, None),
        'crs': crs_def.EPSG_3035,
    },
}

TEST_CASES = [
    ({}, {
        'items': [MAP_1E_2_4X6_6,
                  MAP_1E_3_3X3_3,
                  MAP_1O_2_2X3_6,
                  MAP_1OE_3_7X5_9,
                  MAP_2E_3_3X5_5,
                  MAP_2O_2_2X4_4,
                  MAP_3O_NULL,
                  ],
        'total_count': 7,
        'content_range': (1, 7),
    }),
    ({'reader': settings.ANONYM_USER}, {
        'items': [MAP_1E_2_4X6_6,
                  MAP_1E_3_3X3_3,
                  MAP_1OE_3_7X5_9,
                  MAP_2E_3_3X5_5,
                  ],
        'total_count': 4,
        'content_range': (1, 4),
    }),
    ({'reader': WORKSPACE2}, {
        'items': [MAP_1E_2_4X6_6,
                  MAP_1E_3_3X3_3,
                  MAP_1OE_3_7X5_9,
                  MAP_2E_3_3X5_5,
                  MAP_2O_2_2X4_4,
                  ],
        'total_count': 5,
        'content_range': (1, 5),
    }),
    ({'writer': settings.ANONYM_USER}, {
        'items': [MAP_1E_2_4X6_6,
                  MAP_1E_3_3X3_3,
                  MAP_2E_3_3X5_5,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'writer': WORKSPACE2}, {
        'items': [MAP_1E_2_4X6_6,
                  MAP_1E_3_3X3_3,
                  MAP_2E_3_3X5_5,
                  MAP_2O_2_2X4_4,
                  ],
        'total_count': 4,
        'content_range': (1, 4),
    }),
    ({'full_text_filter': 'dva'}, {
        'items': [MAP_1OE_3_7X5_9,
                  ],
        'total_count': 1,
        'content_range': (1, 1),
    }),
    ({'full_text_filter': 'games'}, {
        'items': [MAP_2E_3_3X5_5,
                  ],
        'total_count': 1,
        'content_range': (1, 1),
    }),
    ({'full_text_filter': 'kun'}, {
        'items': [MAP_1E_2_4X6_6,
                  MAP_1O_2_2X3_6,
                  ],
        'total_count': 2,
        'content_range': (1, 2),
    }),
    ({'full_text_filter': 'jedna'}, {
        'items': [MAP_1OE_3_7X5_9,
                  MAP_2O_2_2X4_4,
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
        'items': [MAP_1E_2_4X6_6,
                  MAP_1O_2_2X3_6,
                  MAP_1OE_3_7X5_9,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'full_text_filter': 'dn'}, {
        'items': [MAP_1E_3_3X3_3,
                  MAP_1OE_3_7X5_9,
                  MAP_2O_2_2X4_4,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'full_text_filter': 'oda', 'ordering_full_text': 'oda', 'order_by_list': ['full_text'], }, {
        'items': [MAP_2O_2_2X4_4,
                  MAP_1E_3_3X3_3,
                  ],
        'total_count': 2,
        'content_range': (1, 2),
    }),
    ({'full_text_filter': 'va kód', 'ordering_full_text': 'va kód', 'order_by_list': ['full_text'], }, {
        'items': [MAP_1OE_3_7X5_9,
                  MAP_1E_3_3X3_3,
                  ],
        'total_count': 2,
        'content_range': (1, 2),
    }),
    ({'order_by_list': ['full_text'], 'ordering_full_text': 'jedna'}, {
        'items': [MAP_1OE_3_7X5_9,
                  MAP_2O_2_2X4_4,
                  MAP_1E_2_4X6_6,
                  MAP_1E_3_3X3_3,
                  MAP_1O_2_2X3_6,
                  MAP_2E_3_3X5_5,
                  MAP_3O_NULL,
                  ],
        'total_count': 7,
        'content_range': (1, 7),
    }),
    ({'full_text_filter': 'dva kun', 'order_by_list': ['full_text'], 'ordering_full_text': 'karel kun'}, {
        'items': [MAP_1O_2_2X3_6,
                  MAP_1E_2_4X6_6,
                  MAP_1OE_3_7X5_9,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'order_by_list': ['title'], }, {
        'items': [MAP_2O_2_2X4_4,
                  MAP_1O_2_2X3_6,
                  MAP_1OE_3_7X5_9,
                  MAP_1E_3_3X3_3,
                  MAP_3O_NULL,
                  MAP_1E_2_4X6_6,
                  MAP_2E_3_3X5_5,
                  ],
        'total_count': 7,
        'content_range': (1, 7),
    }),
    ({'order_by_list': ['last_change'], }, {
        'items': [MAP_3O_NULL,
                  MAP_2O_2_2X4_4,
                  MAP_2E_3_3X5_5,
                  MAP_1OE_3_7X5_9,
                  MAP_1O_2_2X3_6,
                  MAP_1E_3_3X3_3,
                  MAP_1E_2_4X6_6,
                  ],
        'total_count': 7,
        'content_range': (1, 7),
    }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': (1842999, 6322999, 1845001, 6325001),
      'ordering_bbox_crs': crs_def.EPSG_3857,
      }, {'items': [MAP_2E_3_3X5_5,
                    MAP_1E_2_4X6_6,
                    MAP_2O_2_2X4_4,
                    MAP_1O_2_2X3_6,
                    MAP_1E_3_3X3_3,
                    MAP_1OE_3_7X5_9,
                    MAP_3O_NULL,
                    ],
          'total_count': 7,
          'content_range': (1, 7),
          }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': (16.5559417, 49.2828904, 16.573926, 49.2946205),
      # EPSG:3857 (1842999, 6322999, 1845001, 6325001)
      'ordering_bbox_crs': crs_def.EPSG_4326,
      }, {'items': [MAP_2E_3_3X5_5,
                    MAP_1E_2_4X6_6,
                    MAP_2O_2_2X4_4,
                    MAP_1E_3_3X3_3,
                    MAP_1O_2_2X3_6,
                    MAP_1OE_3_7X5_9,
                    MAP_3O_NULL,
                    ],
          'total_count': 7,
          'content_range': (1, 7),
          }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': (-600879.43, -1150642.64, -599437.98, -1149487.13),
      # EPSG:3857 (1842999, 6322999, 1845001, 6325001)
      'ordering_bbox_crs': crs_def.EPSG_5514,
      }, {'items': [MAP_2E_3_3X5_5,
                    MAP_1E_2_4X6_6,
                    MAP_2O_2_2X4_4,
                    MAP_1O_2_2X3_6,
                    MAP_1E_3_3X3_3,
                    MAP_1OE_3_7X5_9,
                    MAP_3O_NULL,
                    ],
          'total_count': 7,
          'content_range': (1, 7),
          }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': (1844001, 6324001, 1844001, 6324001),
      'ordering_bbox_crs': crs_def.EPSG_3857,
      'bbox_filter': (1844001, 6324001, 1844001, 6324001),
      'bbox_filter_crs': crs_def.EPSG_3857,
      }, {'items': [MAP_2E_3_3X5_5,
                    MAP_2O_2_2X4_4,
                    MAP_1E_2_4X6_6,
                    ],
          'total_count': 3,
          'content_range': (1, 3),
          }),
    ({'bbox_filter': (-600665, -1150641, -599439, -1149488),  # EPSG:3857 (1843001, 6323001, 1844999, 6324999)
      'bbox_filter_crs': crs_def.EPSG_5514,
      }, {'items': [MAP_1E_2_4X6_6,
                    MAP_2E_3_3X5_5,
                    MAP_2O_2_2X4_4,
                    ],
          'total_count': 3,
          'content_range': (1, 3),
          }),
    ({'bbox_filter': (176844.09626803786, 5468335.761457844, 176844.09626803786, 5468335.7614578441),
      # EPSG:3857 (1843001, 6323001, 1843001, 6323001)
      'bbox_filter_crs': crs_def.EPSG_32634,
      }, {'items': [MAP_1O_2_2X3_6,
                    MAP_2E_3_3X5_5,
                    MAP_2O_2_2X4_4,
                    ],
          'total_count': 3,
          'content_range': (1, 3),
          }),
    ({'limit': 2}, {
        'items': [MAP_1E_2_4X6_6,
                  MAP_1E_3_3X3_3,
                  # MAP_1O_2_2X3_6,
                  # MAP_1OE_3_7X5_9,
                  # MAP_2E_3_3X5_5,
                  # MAP_2O_2_2X4_4,
                  # MAP_3O_NULL,
                  ],
        'total_count': 7,
        'content_range': (1, 2),
    }),
    ({'offset': 2}, {
        'items': [
            # MAP_1E_2_4X6_6,
            # MAP_1E_3_3X3_3,
            MAP_1O_2_2X3_6,
            MAP_1OE_3_7X5_9,
            MAP_2E_3_3X5_5,
            MAP_2O_2_2X4_4,
            MAP_3O_NULL,
        ],
        'total_count': 7,
        'content_range': (3, 7),
    }),
    ({'limit': 5, 'offset': 5}, {
        'items': [
            # MAP_1E_2_4X6_6,
            # MAP_1E_3_3X3_3,
            # MAP_1O_2_2X3_6,
            # MAP_1OE_3_7X5_9,
            # MAP_2E_3_3X5_5,
            MAP_2O_2_2X4_4,
            MAP_3O_NULL,
        ],
        'total_count': 7,
        'content_range': (6, 7),
    }),
    ({'limit': 2, 'offset': 2}, {
        'items': [
            # MAP_1E_2_4X6_6,
            # MAP_1E_3_3X3_3,
            MAP_1O_2_2X3_6,
            MAP_1OE_3_7X5_9,
            # MAP_2E_3_3X5_5,
            # MAP_2O_2_2X4_4,
            # MAP_3O_NULL,
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
]


def generate_test_cases():
    tc_list = []
    for idx, (query_params, exp_result) in enumerate(TEST_CASES):
        test_case = base_test.TestCaseType(key=f"query-{idx+1}",
                                           params={
                                               'query': query_params,
                                               'exp_result': exp_result,
                                           },
                                           type=EnumTestTypes.MANDATORY,
                                           )
        tc_list.append(test_case)
    return tc_list


@pytest.mark.usefixtures('oauth2_provider_mock')
class TestGet(base_test.TestSingleRestPublication):

    test_cases = generate_test_cases()

    def before_class(self):
        for workspace in WORKSPACES:
            prime_db_schema_client.ensure_user(workspace)
        for publication, publ_params in PUBLICATIONS.items():
            prime_db_schema_client.post_workspace_publication(publication.type, publication.workspace, publication.name,
                                                              actor=publication.workspace, **publ_params)

    def after_class(self, request):
        prime_db_schema_client.clear_workspaces(WORKSPACES)

    def test_query(self, params):
        query_params = params['query']
        exp_result = params['exp_result']
        with app.app_context():
            infos = prime_db_schema_publications.get_publication_infos_with_metainfo(**query_params)
        info_publications = list(infos['items'].keys())
        assert set(info_publications) == set(exp_result['items'])
        assert info_publications == exp_result['items']
        assert infos['total_count'] == exp_result['total_count']
        assert infos['content_range'] == exp_result['content_range']
