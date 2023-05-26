import copy
from dataclasses import dataclass
from enum import Enum, unique
import inspect
import os
from typing import Union, Tuple
import unicodedata
import pytest

import crs as crs_def
from layman import app, settings
from layman.common.prime_db_schema import publications as prime_db_schema_publications
from tests import Publication, EnumTestTypes
from tests.dynamic_data import base_test
from test_tools import process_client, prime_db_schema_client


DIRECTORY = os.path.dirname(os.path.abspath(__file__))
WORKSPACE1 = 'test_select_publications_complex_workspace1'
WORKSPACE2 = 'test_select_publications_complex_workspace2'
WORKSPACE3 = 'test_select_publications_complex_workspace3'
WORKSPACES = [WORKSPACE1, WORKSPACE2, WORKSPACE3]

MAP_1E_BBOX_BF46 = Publication(WORKSPACE1, process_client.MAP_TYPE, 'test_select_publications_map1e')
MAP_1E_BBOX_C3 = Publication(WORKSPACE1, process_client.MAP_TYPE, 'test_select_publications_map1e_3_3x3_3')
MAP_1O_BBOX_BC26 = Publication(WORKSPACE1, process_client.MAP_TYPE, 'test_select_publications_map1o')
MAP_1OE_BBOX_CE79 = Publication(WORKSPACE1, process_client.MAP_TYPE, 'test_select_publications_map1oe')
MAP_2E_BBOX_CE35 = Publication(WORKSPACE2, process_client.MAP_TYPE, 'test_select_publications_map2e')
MAP_2O_BBOX_BD24 = Publication(WORKSPACE2, process_client.MAP_TYPE, 'test_select_publications_map2o')
MAP_3O_BBOX_EMPTY = Publication(WORKSPACE3, process_client.MAP_TYPE, 'test_select_publications_map3o')


@dataclass(frozen=True)
class BBoxClass:
    epsg_3857: Union[Tuple[float], Tuple[int], Tuple[None]] = None
    epsg_4326: Union[Tuple[float], Tuple[int], Tuple[None]] = None
    epsg_5514: Union[Tuple[float], Tuple[int], Tuple[None]] = None
    epsg_32633: Union[Tuple[float], Tuple[int], Tuple[None]] = None
    epsg_32634: Union[Tuple[float], Tuple[int], Tuple[None]] = None
    epsg_3034: Union[Tuple[float], Tuple[int], Tuple[None]] = None
    epsg_3035: Union[Tuple[float], Tuple[int], Tuple[None]] = None


@unique
class BBox(Enum):
    BC26 = BBoxClass(
        # 1842011 6321892 1842988 6326107
        epsg_5514=(-601597.1407428421, -1151286.9441679057, -600665.4471820187, -1148625.2345234894),
    )
    BD24 = BBoxClass(
        # 1841824 6322015 1844176 6323984
        epsg_3034=(4459469.209282893, 2527850.676486253, 4460838.491401795, 2529216.681901061),
    )
    BF46 = BBoxClass(
        epsg_3857=(1842000, 6324000, 1846000, 6326000),
    )
    C3 = BBoxClass(
        # 1843000 6323000
        epsg_4326=(16.55595068632278, 49.28289621550056, 16.55595068632278, 49.28289621550056),
        # 1843001, 6323001
        epsg_32634=(176844.09626803786, 5468335.761457844, 176844.09626803786, 5468335.761457844),
    )
    CE35 = BBoxClass(
        epsg_3857=(1843000, 6323000, 1845000, 6325000),
        # 1843006 6322882 1844993 6325117
        epsg_32634=(176844.09626803786, 5468335.761457844, 178226.55642100016, 5469714.707582928),
        # 1842999, 6322999, 1845001, 6325001
        epsg_4326=(16.5559417, 49.2828904, 16.573926, 49.2946205),
        # 1842999, 6322999, 1845001, 6325001
        epsg_5514=(-600879.43, -1150642.64, -599437.98, -1149487.13),
    )
    CE79 = BBoxClass(
        # 1842958 6327000 1845041 6328999
        epsg_32633=(613077.7082822081, 5462674.538979379, 614410.4777841105, 5464003.656058598),
    )
    D4 = BBoxClass(
        epsg_3857=(1844000, 6324000, 1844000, 6324000),
    )
    EMPTY = BBoxClass(
        epsg_3035=(None, None, None, None),
    )


PUBLICATIONS = {
    MAP_1E_BBOX_BF46: {
        'title': 'Příliš žluťoučký Kůň úpěl ďábelské ódy',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {settings.RIGHTS_EVERYONE_ROLE}},
        'bbox': BBox.BF46.value.epsg_3857,
        'crs': crs_def.EPSG_3857,
    },
    MAP_1E_BBOX_C3: {
        'title': 'Jednobodová vrstva Kodaň',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {settings.RIGHTS_EVERYONE_ROLE}},
        'bbox': BBox.C3.value.epsg_4326,
        'crs': crs_def.EPSG_4326,
    },
    MAP_1O_BBOX_BC26: {
        'title': 'Ďůlek kun Karel',
        'access_rights': {'read': {WORKSPACE1},
                          'write': {WORKSPACE1}},
        'bbox': BBox.BC26.value.epsg_5514,
        'crs': crs_def.EPSG_5514,
    },
    MAP_1OE_BBOX_CE79: {
        'title': 'jedna dva tři čtyři kód',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {WORKSPACE1}},
        'bbox': BBox.CE79.value.epsg_32633,
        'crs': crs_def.EPSG_32633,
    },
    MAP_2E_BBOX_CE35: {
        'title': 'Svíčky is the best game',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {settings.RIGHTS_EVERYONE_ROLE}},
        'bbox': BBox.CE35.value.epsg_32634,
        'crs': crs_def.EPSG_32634,
    },
    MAP_2O_BBOX_BD24: {
        'title': 'druhá mapa JeDnA óda',
        'access_rights': {'read': {WORKSPACE2},
                          'write': {WORKSPACE2}},
        'bbox': BBox.BD24.value.epsg_3034,
        'crs': crs_def.EPSG_3034,
    },
    MAP_3O_BBOX_EMPTY: {
        'title': 'Nullový bounding box',
        'access_rights': {'read': {WORKSPACE3},
                          'write': {WORKSPACE3}},
        'bbox': BBox.EMPTY.value.epsg_3035,
        'crs': crs_def.EPSG_3035,
    },
}

INTERNAL_TEST_CASES = [
    ({}, {
        'items': [MAP_1E_BBOX_BF46,
                  MAP_1E_BBOX_C3,
                  MAP_1O_BBOX_BC26,
                  MAP_1OE_BBOX_CE79,
                  MAP_2E_BBOX_CE35,
                  MAP_2O_BBOX_BD24,
                  MAP_3O_BBOX_EMPTY,
                  ],
        'total_count': 7,
        'content_range': (1, 7),
    }),
    ({'reader': settings.ANONYM_USER}, {
        'items': [MAP_1E_BBOX_BF46,
                  MAP_1E_BBOX_C3,
                  MAP_1OE_BBOX_CE79,
                  MAP_2E_BBOX_CE35,
                  ],
        'total_count': 4,
        'content_range': (1, 4),
    }),
    ({'reader': WORKSPACE2}, {
        'items': [MAP_1E_BBOX_BF46,
                  MAP_1E_BBOX_C3,
                  MAP_1OE_BBOX_CE79,
                  MAP_2E_BBOX_CE35,
                  MAP_2O_BBOX_BD24,
                  ],
        'total_count': 5,
        'content_range': (1, 5),
    }),
    ({'writer': settings.ANONYM_USER}, {
        'items': [MAP_1E_BBOX_BF46,
                  MAP_1E_BBOX_C3,
                  MAP_2E_BBOX_CE35,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'writer': WORKSPACE2}, {
        'items': [MAP_1E_BBOX_BF46,
                  MAP_1E_BBOX_C3,
                  MAP_2E_BBOX_CE35,
                  MAP_2O_BBOX_BD24,
                  ],
        'total_count': 4,
        'content_range': (1, 4),
    }),
    ({'full_text_filter': 'dva'}, {
        'items': [MAP_1OE_BBOX_CE79,
                  ],
        'total_count': 1,
        'content_range': (1, 1),
    }),
    ({'full_text_filter': 'games'}, {
        'items': [MAP_2E_BBOX_CE35,
                  ],
        'total_count': 1,
        'content_range': (1, 1),
    }),
    ({'full_text_filter': 'kun'}, {
        'items': [MAP_1E_BBOX_BF46,
                  MAP_1O_BBOX_BC26,
                  ],
        'total_count': 2,
        'content_range': (1, 2),
    }),
    ({'full_text_filter': 'jedna'}, {
        'items': [MAP_1OE_BBOX_CE79,
                  MAP_2O_BBOX_BD24,
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
        'items': [MAP_1E_BBOX_BF46,
                  MAP_1O_BBOX_BC26,
                  MAP_1OE_BBOX_CE79,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'full_text_filter': 'dn'}, {
        'items': [MAP_1E_BBOX_C3,
                  MAP_1OE_BBOX_CE79,
                  MAP_2O_BBOX_BD24,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'full_text_filter': 'oda', 'ordering_full_text': 'oda', 'order_by_list': ['full_text'], }, {
        'items': [MAP_2O_BBOX_BD24,
                  MAP_1E_BBOX_C3,
                  ],
        'total_count': 2,
        'content_range': (1, 2),
    }),
    ({'full_text_filter': 'va kód', 'ordering_full_text': 'va kód', 'order_by_list': ['full_text'], }, {
        'items': [MAP_1OE_BBOX_CE79,
                  MAP_1E_BBOX_C3,
                  ],
        'total_count': 2,
        'content_range': (1, 2),
    }),
    ({'order_by_list': ['full_text'], 'ordering_full_text': 'jedna'}, {
        'items': [MAP_1OE_BBOX_CE79,
                  MAP_2O_BBOX_BD24,
                  MAP_1E_BBOX_BF46,
                  MAP_1E_BBOX_C3,
                  MAP_1O_BBOX_BC26,
                  MAP_2E_BBOX_CE35,
                  MAP_3O_BBOX_EMPTY,
                  ],
        'total_count': 7,
        'content_range': (1, 7),
    }),
    ({'full_text_filter': 'dva kun', 'order_by_list': ['full_text'], 'ordering_full_text': 'karel kun'}, {
        'items': [MAP_1O_BBOX_BC26,
                  MAP_1E_BBOX_BF46,
                  MAP_1OE_BBOX_CE79,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'order_by_list': ['title'], }, {
        'items': [MAP_2O_BBOX_BD24,
                  MAP_1O_BBOX_BC26,
                  MAP_1OE_BBOX_CE79,
                  MAP_1E_BBOX_C3,
                  MAP_3O_BBOX_EMPTY,
                  MAP_1E_BBOX_BF46,
                  MAP_2E_BBOX_CE35,
                  ],
        'total_count': 7,
        'content_range': (1, 7),
    }),
    ({'order_by_list': ['last_change'], }, {
        'items': [MAP_3O_BBOX_EMPTY,
                  MAP_2O_BBOX_BD24,
                  MAP_2E_BBOX_CE35,
                  MAP_1OE_BBOX_CE79,
                  MAP_1O_BBOX_BC26,
                  MAP_1E_BBOX_C3,
                  MAP_1E_BBOX_BF46,
                  ],
        'total_count': 7,
        'content_range': (1, 7),
    }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': BBox.CE35.value.epsg_3857,
      'ordering_bbox_crs': crs_def.EPSG_3857,
      }, {'items': [MAP_2E_BBOX_CE35,   # area 4
                    MAP_1E_BBOX_BF46,   # area 1
                    MAP_2O_BBOX_BD24,   # area 1
                    MAP_1O_BBOX_BC26,   # area 0, line 2
                    MAP_1E_BBOX_C3,     # area 0, point
                    MAP_1OE_BBOX_CE79,  # no intersection
                    MAP_3O_BBOX_EMPTY,  # no intersection
                    ],
          'total_count': 7,
          'content_range': (1, 7),
          }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': BBox.CE35.value.epsg_4326,
      'ordering_bbox_crs': crs_def.EPSG_4326,
      }, {'items': [MAP_2E_BBOX_CE35,   # area 4
                    MAP_1E_BBOX_BF46,   # area 1
                    MAP_2O_BBOX_BD24,   # area 1
                    MAP_1E_BBOX_C3,     # area 0, point
                    MAP_1O_BBOX_BC26,   # area 0, line 2
                    MAP_1OE_BBOX_CE79,  # no intersection
                    MAP_3O_BBOX_EMPTY,  # no intersection
                    ],
          'total_count': 7,
          'content_range': (1, 7),
          }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': BBox.CE35.value.epsg_5514,
      'ordering_bbox_crs': crs_def.EPSG_5514,
      }, {'items': [MAP_2E_BBOX_CE35,   # area 4
                    MAP_1E_BBOX_BF46,   # area 1
                    MAP_2O_BBOX_BD24,   # area 1
                    MAP_1O_BBOX_BC26,   # area 0, line 2
                    MAP_1E_BBOX_C3,     # area 0, point
                    MAP_1OE_BBOX_CE79,  # no intersection
                    MAP_3O_BBOX_EMPTY,  # no intersection
                    ],
          'total_count': 7,
          'content_range': (1, 7),
          }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': BBox.D4.value.epsg_3857,
      'ordering_bbox_crs': crs_def.EPSG_3857,
      'bbox_filter': BBox.D4.value.epsg_3857,
      'bbox_filter_crs': crs_def.EPSG_3857,
      }, {'items': [MAP_2E_BBOX_CE35,  # area 0, point
                    MAP_2O_BBOX_BD24,  # area 0, point
                    MAP_1E_BBOX_BF46,  # area 0, point
                    ],
          'total_count': 3,
          'content_range': (1, 3),
          }),
    ({'bbox_filter': BBox.CE35.value.epsg_5514,
      'bbox_filter_crs': crs_def.EPSG_5514,
      }, {'items': [MAP_1E_BBOX_BF46,  # area 1
                    MAP_1E_BBOX_C3,    # area 0, point
                    MAP_1O_BBOX_BC26,  # area 0, line 2
                    MAP_2E_BBOX_CE35,  # area 4
                    MAP_2O_BBOX_BD24,  # area 1
                    ],
          'total_count': 5,
          'content_range': (1, 5),
          }),
    ({'bbox_filter': BBox.C3.value.epsg_32634,
      'bbox_filter_crs': crs_def.EPSG_32634,
      }, {'items': [MAP_1O_BBOX_BC26,  # area 0, point
                    MAP_2E_BBOX_CE35,  # area 0, point
                    MAP_2O_BBOX_BD24,  # area 0, point
                    ],
          'total_count': 3,
          'content_range': (1, 3),
          }),
    ({'limit': 2}, {
        'items': [MAP_1E_BBOX_BF46,
                  MAP_1E_BBOX_C3,
                  # MAP_1O_BBOX_BC26,
                  # MAP_1OE_BBOX_CE79,
                  # MAP_2E_BBOX_CE35,
                  # MAP_2O_BBOX_BD24,
                  # MAP_3O_BBOX_EMPTY,
                  ],
        'total_count': 7,
        'content_range': (1, 2),
    }),
    ({'offset': 2}, {
        'items': [
            # MAP_1E_BBOX_BF46,
            # MAP_1E_BBOX_C3,
            MAP_1O_BBOX_BC26,
            MAP_1OE_BBOX_CE79,
            MAP_2E_BBOX_CE35,
            MAP_2O_BBOX_BD24,
            MAP_3O_BBOX_EMPTY,
        ],
        'total_count': 7,
        'content_range': (3, 7),
    }),
    ({'limit': 5, 'offset': 5}, {
        'items': [
            # MAP_1E_BBOX_BF46,
            # MAP_1E_BBOX_C3,
            # MAP_1O_BBOX_BC26,
            # MAP_1OE_BBOX_CE79,
            # MAP_2E_BBOX_CE35,
            MAP_2O_BBOX_BD24,
            MAP_3O_BBOX_EMPTY,
        ],
        'total_count': 7,
        'content_range': (6, 7),
    }),
    ({'limit': 2, 'offset': 2}, {
        'items': [
            # MAP_1E_BBOX_BF46,
            # MAP_1E_BBOX_C3,
            MAP_1O_BBOX_BC26,
            MAP_1OE_BBOX_CE79,
            # MAP_2E_BBOX_CE35,
            # MAP_2O_BBOX_BD24,
            # MAP_3O_BBOX_EMPTY,
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

REST_TEST_CASES = [
    ({}, {
        'items': [MAP_1E_BBOX_BF46,
                  MAP_1E_BBOX_C3,
                  MAP_1OE_BBOX_CE79,
                  MAP_2E_BBOX_CE35,
                  ],
        'total_count': 4,
        'content_range': (1, 4),
    })
]


def pytest_generate_tests(metafunc):
    # https://docs.pytest.org/en/6.2.x/parametrize.html#pytest-generate-tests
    cls = metafunc.cls
    test_fn = metafunc.function
    arg_names = [a for a in inspect.getfullargspec(test_fn).args if a != 'self']
    argvalues = []
    ids = []

    test_cases = cls.test_cases[test_fn.__name__]
    for test_case in test_cases:
        assert not test_case.publication, f"Not yet implemented"
        assert not test_case.publication_type, f"Not yet implemented"
        assert not test_case.key, f"Not yet implemented"
        assert not test_case.rest_method, f"Not yet implemented"
        assert not test_case.rest_args, f"Not yet implemented"
        assert not test_case.specific_params, f"Not yet implemented"
        assert not test_case.specific_types, f"Not yet implemented"
        assert not test_case.parametrization, f"Not yet implemented"
        assert not test_case.post_before_patch_args, f"Not yet implemented"
        assert test_case.type == EnumTestTypes.MANDATORY, f"Other types then MANDATORY are not implemented yet"
        arg_name_to_value = {
            'params': copy.deepcopy(test_case.params),
        }
        arg_values = [arg_name_to_value[n] for n in arg_names]

        argvalues.append(pytest.param(*arg_values, marks=test_case.marks))
        ids.append(test_case.pytest_id)
    metafunc.parametrize(
        argnames=', '.join(arg_names),
        argvalues=argvalues,
        ids=ids,
    )


def generate_test_cases(test_cases):
    tc_list = []
    for idx, (query_params, exp_result) in enumerate(test_cases):
        test_case = base_test.TestCaseType(pytest_id=f"query-{idx+1}",
                                           params={
                                               'query': query_params,
                                               'exp_result': exp_result,
                                           },
                                           type=EnumTestTypes.MANDATORY,
                                           )
        tc_list.append(test_case)
    return tc_list


@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
class TestGet:
    test_cases = {
        'test_internal_query': generate_test_cases(INTERNAL_TEST_CASES),
        'test_rest_query': generate_test_cases(REST_TEST_CASES),
    }

    usernames_to_reserve = WORKSPACES

    @pytest.fixture(scope='class', autouse=True)
    def class_fixture(self):
        for username in self.usernames_to_reserve:
            headers = process_client.get_authz_headers(username)
            process_client.ensure_reserved_username(username, headers=headers)

        TestGet.before_class()
        yield
        TestGet.after_class()

    @staticmethod
    def before_class():
        for publication, publ_params in PUBLICATIONS.items():
            prime_db_schema_client.post_workspace_publication(publication.type, publication.workspace, publication.name,
                                                              actor=publication.workspace, **publ_params)

    @staticmethod
    def after_class():
        prime_db_schema_client.clear_workspaces(WORKSPACES)

    def test_internal_query(self, params):
        query_params = params['query']
        exp_result = params['exp_result']
        with app.app_context():
            infos = prime_db_schema_publications.get_publication_infos_with_metainfo(**query_params)
        info_publications = list(infos['items'].keys())
        assert set(info_publications) == set(exp_result['items'])
        assert info_publications == exp_result['items']
        assert infos['total_count'] == exp_result['total_count']
        assert infos['content_range'] == exp_result['content_range']

    def test_rest_query(self, params):
        query_params = params['query']

        exp_result = params['exp_result']

        info_publications_response = process_client.get_publications_response(process_client.MAP_TYPE,
                                                                              query_params=query_params)
        info_publications_json = info_publications_response.json()
        info_publications = [Publication(item['workspace'], process_client.MAP_TYPE, item['name'])
                             for item in info_publications_json]

        assert set(info_publications) == set(exp_result['items'])
        assert info_publications == exp_result['items']
        assert info_publications_response.headers['X-Total-Count'] == f"{exp_result['total_count']}"
        content_range_str = f"items {exp_result['content_range'][0]}-{exp_result['content_range'][1]}/{exp_result['total_count']}"
        assert info_publications_response.headers['Content-Range'] == content_range_str
