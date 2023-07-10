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
WS_USER1 = 'test_dynamic_multi_ws1'
WS_USER2 = 'test_dynamic_multi_ws2'
WS_USER3 = 'test_dynamic_multi_ws3'
WS_PUBL = 'test_dynamic_multi_ws_public'
USERNAMES = [WS_USER1, WS_USER2, WS_USER3]
WORKSPACES = USERNAMES + [WS_PUBL]

AUTHN_HEADERS_USER1 = process_client.get_authz_headers(WS_USER1)
AUTHN_HEADERS_USER2 = process_client.get_authz_headers(WS_USER2)
AUTHN_HEADERS_USER3 = process_client.get_authz_headers(WS_USER3)

MAP1_WS1_REWE_BBOX_BF46 = Publication(WS_USER1, process_client.MAP_TYPE, 'test_dynamic_map1')
MAP2_WS1_REWE_BBOX_C3 = Publication(WS_USER1, process_client.MAP_TYPE, 'test_dynamic_map2')
MAP3_WS1_ROWO_BBOX_BC26 = Publication(WS_USER1, process_client.MAP_TYPE, 'test_dynamic_map3')
MAP4_WS1_REWO_BBOX_CE79 = Publication(WS_USER1, process_client.MAP_TYPE, 'test_dynamic_map4')
MAP5_WS2_REWE_BBOX_CE35 = Publication(WS_USER2, process_client.MAP_TYPE, 'test_dynamic_map5')
MAP6_WS2_ROWO_BBOX_BD24 = Publication(WS_USER2, process_client.MAP_TYPE, 'test_dynamic_map6')
MAP7_WS3_ROWO_BBOX_EMPTY = Publication(WS_USER3, process_client.MAP_TYPE, 'test_dynamic_map7')
LAY1_WSP_REWE_BBOX_BC26 = Publication(WS_PUBL, process_client.LAYER_TYPE, 'test_dynamic_lyr1')
LAY2_WS1_R2WO_BBOX_BC26 = Publication(WS_USER1, process_client.LAYER_TYPE, 'test_dynamic_lyr2')


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
    MAP1_WS1_REWE_BBOX_BF46: {
        'title': 'Příliš žluťoučký Kůň úpěl ďábelské ódy',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {settings.RIGHTS_EVERYONE_ROLE}},
        'bbox': BBox.BF46.value.epsg_3857,
        'crs': crs_def.EPSG_3857,
    },
    MAP2_WS1_REWE_BBOX_C3: {
        'title': 'Jednobodová vrstva Kodaň',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {settings.RIGHTS_EVERYONE_ROLE}},
        'bbox': BBox.C3.value.epsg_4326,
        'crs': crs_def.EPSG_4326,
    },
    MAP3_WS1_ROWO_BBOX_BC26: {
        'title': 'Ďůlek kun Karel',
        'access_rights': {'read': {WS_USER1},
                          'write': {WS_USER1}},
        'bbox': BBox.BC26.value.epsg_5514,
        'crs': crs_def.EPSG_5514,
    },
    MAP4_WS1_REWO_BBOX_CE79: {
        'title': 'jedna dva tři čtyři kód',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {WS_USER1}},
        'bbox': BBox.CE79.value.epsg_32633,
        'crs': crs_def.EPSG_32633,
    },
    MAP5_WS2_REWE_BBOX_CE35: {
        'title': 'Svíčky is the best game',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {settings.RIGHTS_EVERYONE_ROLE}},
        'bbox': BBox.CE35.value.epsg_32634,
        'crs': crs_def.EPSG_32634,
    },
    MAP6_WS2_ROWO_BBOX_BD24: {
        'title': 'druhá mapa JeDnA óda',
        'access_rights': {'read': {WS_USER2},
                          'write': {WS_USER2}},
        'bbox': BBox.BD24.value.epsg_3034,
        'crs': crs_def.EPSG_3034,
    },
    MAP7_WS3_ROWO_BBOX_EMPTY: {
        'title': 'Nullový bounding box',
        'access_rights': {'read': {WS_USER3},
                          'write': {WS_USER3}},
        'bbox': BBox.EMPTY.value.epsg_3035,
        'crs': crs_def.EPSG_3035,
    },
    LAY1_WSP_REWE_BBOX_BC26: {
        'title': 'Hezká vektorová vrstva, óda na Křováka',
        'access_rights': {'read': {settings.RIGHTS_EVERYONE_ROLE},
                          'write': {settings.RIGHTS_EVERYONE_ROLE}},
        'bbox': BBox.BC26.value.epsg_5514,
        'crs': crs_def.EPSG_5514,
        'geodata_type': 'vector',
        'wfs_wms_status': 'AVAILABLE',
    },
    LAY2_WS1_R2WO_BBOX_BC26: {
        'title': 'Vektorová vrstva',
        'access_rights': {'read': {WS_USER1, WS_USER2},
                          'write': {WS_USER1}},
        'bbox': BBox.BC26.value.epsg_5514,
        'crs': crs_def.EPSG_5514,
        'geodata_type': 'vector',
        'wfs_wms_status': 'AVAILABLE',
    },
}

INTERNAL_TEST_CASES = [
    ({}, {
        'items': [LAY2_WS1_R2WO_BBOX_BC26,
                  MAP1_WS1_REWE_BBOX_BF46,
                  MAP2_WS1_REWE_BBOX_C3,
                  MAP3_WS1_ROWO_BBOX_BC26,
                  MAP4_WS1_REWO_BBOX_CE79,
                  MAP5_WS2_REWE_BBOX_CE35,
                  MAP6_WS2_ROWO_BBOX_BD24,
                  MAP7_WS3_ROWO_BBOX_EMPTY,
                  LAY1_WSP_REWE_BBOX_BC26,
                  ],
        'total_count': 9,
        'content_range': (1, 9),
    }),
    ({'reader': settings.ANONYM_USER}, {
        'items': [MAP1_WS1_REWE_BBOX_BF46,
                  MAP2_WS1_REWE_BBOX_C3,
                  MAP4_WS1_REWO_BBOX_CE79,
                  MAP5_WS2_REWE_BBOX_CE35,
                  LAY1_WSP_REWE_BBOX_BC26,
                  ],
        'total_count': 5,
        'content_range': (1, 5),
    }),
    ({'reader': WS_USER2}, {
        'items': [LAY2_WS1_R2WO_BBOX_BC26,
                  MAP1_WS1_REWE_BBOX_BF46,
                  MAP2_WS1_REWE_BBOX_C3,
                  MAP4_WS1_REWO_BBOX_CE79,
                  MAP5_WS2_REWE_BBOX_CE35,
                  MAP6_WS2_ROWO_BBOX_BD24,
                  LAY1_WSP_REWE_BBOX_BC26,
                  ],
        'total_count': 7,
        'content_range': (1, 7),
    }),
    ({'writer': settings.ANONYM_USER}, {
        'items': [MAP1_WS1_REWE_BBOX_BF46,
                  MAP2_WS1_REWE_BBOX_C3,
                  MAP5_WS2_REWE_BBOX_CE35,
                  LAY1_WSP_REWE_BBOX_BC26,
                  ],
        'total_count': 4,
        'content_range': (1, 4),
    }),
    ({'writer': WS_USER2}, {
        'items': [MAP1_WS1_REWE_BBOX_BF46,
                  MAP2_WS1_REWE_BBOX_C3,
                  MAP5_WS2_REWE_BBOX_CE35,
                  MAP6_WS2_ROWO_BBOX_BD24,
                  LAY1_WSP_REWE_BBOX_BC26,
                  ],
        'total_count': 5,
        'content_range': (1, 5),
    }),
    ({'full_text_filter': 'dva'}, {
        'items': [MAP4_WS1_REWO_BBOX_CE79,
                  ],
        'total_count': 1,
        'content_range': (1, 1),
    }),
    ({'full_text_filter': 'games'}, {
        'items': [MAP5_WS2_REWE_BBOX_CE35,
                  ],
        'total_count': 1,
        'content_range': (1, 1),
    }),
    ({'full_text_filter': 'kun'}, {
        'items': [MAP1_WS1_REWE_BBOX_BF46,
                  MAP3_WS1_ROWO_BBOX_BC26,
                  ],
        'total_count': 2,
        'content_range': (1, 2),
    }),
    ({'full_text_filter': 'jedna'}, {
        'items': [MAP4_WS1_REWO_BBOX_CE79,
                  MAP6_WS2_ROWO_BBOX_BD24,
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
        'items': [MAP1_WS1_REWE_BBOX_BF46,
                  MAP3_WS1_ROWO_BBOX_BC26,
                  MAP4_WS1_REWO_BBOX_CE79,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'full_text_filter': 'dn'}, {
        'items': [MAP2_WS1_REWE_BBOX_C3,
                  MAP4_WS1_REWO_BBOX_CE79,
                  MAP6_WS2_ROWO_BBOX_BD24,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'full_text_filter': 'oda', 'ordering_full_text': 'oda', 'order_by_list': ['full_text'], }, {
        'items': [MAP6_WS2_ROWO_BBOX_BD24,
                  LAY1_WSP_REWE_BBOX_BC26,
                  MAP2_WS1_REWE_BBOX_C3,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'full_text_filter': 'va kód', 'ordering_full_text': 'va kód', 'order_by_list': ['full_text'], }, {
        'items': [MAP4_WS1_REWO_BBOX_CE79,
                  MAP2_WS1_REWE_BBOX_C3,
                  ],
        'total_count': 2,
        'content_range': (1, 2),
    }),
    ({'order_by_list': ['full_text'], 'ordering_full_text': 'jedna'}, {
        'items': [MAP4_WS1_REWO_BBOX_CE79,
                  MAP6_WS2_ROWO_BBOX_BD24,
                  LAY2_WS1_R2WO_BBOX_BC26,
                  MAP1_WS1_REWE_BBOX_BF46,
                  MAP2_WS1_REWE_BBOX_C3,
                  MAP3_WS1_ROWO_BBOX_BC26,
                  MAP5_WS2_REWE_BBOX_CE35,
                  MAP7_WS3_ROWO_BBOX_EMPTY,
                  LAY1_WSP_REWE_BBOX_BC26,
                  ],
        'total_count': 9,
        'content_range': (1, 9),
    }),
    ({'full_text_filter': 'dva kun', 'order_by_list': ['full_text'], 'ordering_full_text': 'karel kun'}, {
        'items': [MAP3_WS1_ROWO_BBOX_BC26,
                  MAP1_WS1_REWE_BBOX_BF46,
                  MAP4_WS1_REWO_BBOX_CE79,
                  ],
        'total_count': 3,
        'content_range': (1, 3),
    }),
    ({'order_by_list': ['title'], }, {
        'items': [MAP6_WS2_ROWO_BBOX_BD24,
                  MAP3_WS1_ROWO_BBOX_BC26,
                  LAY1_WSP_REWE_BBOX_BC26,
                  MAP4_WS1_REWO_BBOX_CE79,
                  MAP2_WS1_REWE_BBOX_C3,
                  MAP7_WS3_ROWO_BBOX_EMPTY,
                  MAP1_WS1_REWE_BBOX_BF46,
                  MAP5_WS2_REWE_BBOX_CE35,
                  LAY2_WS1_R2WO_BBOX_BC26,
                  ],
        'total_count': 9,
        'content_range': (1, 9),
    }),
    ({'order_by_list': ['last_change'], }, {
        'items': [LAY2_WS1_R2WO_BBOX_BC26,
                  LAY1_WSP_REWE_BBOX_BC26,
                  MAP7_WS3_ROWO_BBOX_EMPTY,
                  MAP6_WS2_ROWO_BBOX_BD24,
                  MAP5_WS2_REWE_BBOX_CE35,
                  MAP4_WS1_REWO_BBOX_CE79,
                  MAP3_WS1_ROWO_BBOX_BC26,
                  MAP2_WS1_REWE_BBOX_C3,
                  MAP1_WS1_REWE_BBOX_BF46,
                  ],
        'total_count': 9,
        'content_range': (1, 9),
    }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': BBox.CE35.value.epsg_3857,
      'ordering_bbox_crs': crs_def.EPSG_3857,
      }, {'items': [MAP5_WS2_REWE_BBOX_CE35,  # area 4
                    MAP1_WS1_REWE_BBOX_BF46,  # area 1
                    MAP6_WS2_ROWO_BBOX_BD24,  # area 1
                    LAY2_WS1_R2WO_BBOX_BC26,  # area 0, line 2
                    MAP3_WS1_ROWO_BBOX_BC26,  # area 0, line 2
                    LAY1_WSP_REWE_BBOX_BC26,  # area 0, line 2
                    MAP2_WS1_REWE_BBOX_C3,  # area 0, point
                    MAP4_WS1_REWO_BBOX_CE79,  # no intersection
                    MAP7_WS3_ROWO_BBOX_EMPTY,  # no intersection
                    ],
          'total_count': 9,
          'content_range': (1, 9),
          }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': BBox.CE35.value.epsg_4326,
      'ordering_bbox_crs': crs_def.EPSG_4326,
      }, {'items': [MAP5_WS2_REWE_BBOX_CE35,  # area 4
                    MAP1_WS1_REWE_BBOX_BF46,  # area 1
                    MAP6_WS2_ROWO_BBOX_BD24,  # area 1
                    MAP2_WS1_REWE_BBOX_C3,  # area 0, point
                    LAY2_WS1_R2WO_BBOX_BC26,  # area 0, line 2
                    MAP3_WS1_ROWO_BBOX_BC26,  # area 0, line 2
                    LAY1_WSP_REWE_BBOX_BC26,  # area 0, line 2
                    MAP4_WS1_REWO_BBOX_CE79,  # no intersection
                    MAP7_WS3_ROWO_BBOX_EMPTY,  # no intersection
                    ],
          'total_count': 9,
          'content_range': (1, 9),
          }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': BBox.CE35.value.epsg_5514,
      'ordering_bbox_crs': crs_def.EPSG_5514,
      }, {'items': [MAP5_WS2_REWE_BBOX_CE35,  # area 4
                    MAP1_WS1_REWE_BBOX_BF46,  # area 1
                    MAP6_WS2_ROWO_BBOX_BD24,  # area 1
                    LAY2_WS1_R2WO_BBOX_BC26,  # area 0, line 2
                    MAP3_WS1_ROWO_BBOX_BC26,  # area 0, line 2
                    LAY1_WSP_REWE_BBOX_BC26,  # area 0, line 2
                    MAP2_WS1_REWE_BBOX_C3,  # area 0, point
                    MAP4_WS1_REWO_BBOX_CE79,  # no intersection
                    MAP7_WS3_ROWO_BBOX_EMPTY,  # no intersection
                    ],
          'total_count': 9,
          'content_range': (1, 9),
          }),
    ({'order_by_list': ['bbox'],
      'ordering_bbox': BBox.D4.value.epsg_3857,
      'ordering_bbox_crs': crs_def.EPSG_3857,
      'bbox_filter': BBox.D4.value.epsg_3857,
      'bbox_filter_crs': crs_def.EPSG_3857,
      }, {'items': [MAP5_WS2_REWE_BBOX_CE35,  # area 0, point
                    MAP6_WS2_ROWO_BBOX_BD24,  # area 0, point
                    MAP1_WS1_REWE_BBOX_BF46,  # area 0, point
                    ],
          'total_count': 3,
          'content_range': (1, 3),
          }),
    ({'bbox_filter': BBox.CE35.value.epsg_5514,
      'bbox_filter_crs': crs_def.EPSG_5514,
      }, {'items': [LAY2_WS1_R2WO_BBOX_BC26,  # area 0, line 2
                    MAP1_WS1_REWE_BBOX_BF46,  # area 1
                    MAP2_WS1_REWE_BBOX_C3,  # area 0, point
                    MAP3_WS1_ROWO_BBOX_BC26,  # area 0, line 2
                    MAP5_WS2_REWE_BBOX_CE35,  # area 4
                    MAP6_WS2_ROWO_BBOX_BD24,  # area 1
                    LAY1_WSP_REWE_BBOX_BC26,  # area 0, line 2
                    ],
          'total_count': 7,
          'content_range': (1, 7),
          }),
    ({'bbox_filter': BBox.C3.value.epsg_32634,
      'bbox_filter_crs': crs_def.EPSG_32634,
      }, {'items': [LAY2_WS1_R2WO_BBOX_BC26,  # area 0, line 2
                    MAP3_WS1_ROWO_BBOX_BC26,  # area 0, point
                    MAP5_WS2_REWE_BBOX_CE35,  # area 0, point
                    MAP6_WS2_ROWO_BBOX_BD24,  # area 0, point
                    LAY1_WSP_REWE_BBOX_BC26,  # area 0, point
                    ],
          'total_count': 5,
          'content_range': (1, 5),
          }),
    ({'limit': 2}, {
        'items': [LAY2_WS1_R2WO_BBOX_BC26,
                  MAP1_WS1_REWE_BBOX_BF46,
                  # MAP2_WS1_REWE_BBOX_C3,
                  # MAP3_WS1_ROWO_BBOX_BC26,
                  # MAP4_WS1_REWO_BBOX_CE79,
                  # MAP5_WS2_REWE_BBOX_CE35,
                  # MAP6_WS2_ROWO_BBOX_BD24,
                  # MAP7_WS3_ROWO_BBOX_EMPTY,
                  # LAY1_WSP_REWE_BBOX_BC26,
                  ],
        'total_count': 9,
        'content_range': (1, 2),
    }),
    ({'offset': 2}, {
        'items': [
            # LAY2_WS1_R2WO_BBOX_BC26
            # MAP1_WS1_REWE_BBOX_BF46,
            MAP2_WS1_REWE_BBOX_C3,
            MAP3_WS1_ROWO_BBOX_BC26,
            MAP4_WS1_REWO_BBOX_CE79,
            MAP5_WS2_REWE_BBOX_CE35,
            MAP6_WS2_ROWO_BBOX_BD24,
            MAP7_WS3_ROWO_BBOX_EMPTY,
            LAY1_WSP_REWE_BBOX_BC26,
        ],
        'total_count': 9,
        'content_range': (3, 9),
    }),
    ({'limit': 5, 'offset': 6}, {
        'items': [
            # LAY1_WSP_REWE_BBOX_BC26,
            # MAP1_WS1_REWE_BBOX_BF46,
            # MAP2_WS1_REWE_BBOX_C3,
            # MAP3_WS1_ROWO_BBOX_BC26,
            # MAP4_WS1_REWO_BBOX_CE79,
            # MAP5_WS2_REWE_BBOX_CE35,
            MAP6_WS2_ROWO_BBOX_BD24,
            MAP7_WS3_ROWO_BBOX_EMPTY,
            LAY1_WSP_REWE_BBOX_BC26,
        ],
        'total_count': 9,
        'content_range': (7, 9),
    }),
    ({'limit': 2, 'offset': 2}, {
        'items': [
            # LAY1_WSP_REWE_BBOX_BC26
            # MAP1_WS1_REWE_BBOX_BF46,
            MAP2_WS1_REWE_BBOX_C3,
            MAP3_WS1_ROWO_BBOX_BC26,
            # MAP4_WS1_REWO_BBOX_CE79,
            # MAP5_WS2_REWE_BBOX_CE35,
            # MAP6_WS2_ROWO_BBOX_BD24,
            # MAP7_WS3_ROWO_BBOX_EMPTY,
            # LAY1_WSP_REWE_BBOX_BC26,
        ],
        'total_count': 9,
        'content_range': (3, 4),
    }),
    ({'limit': 0, 'offset': 0}, {
        'items': [
        ],
        'total_count': 9,
        'content_range': (0, 0),
    }),
]

REST_TEST_CASES = [
    ({'headers': {},
      'workspace_type_list': [
          (None, process_client.MAP_TYPE),
      ],
      'rest_params': {},
      }, [MAP1_WS1_REWE_BBOX_BF46,
          MAP2_WS1_REWE_BBOX_C3,
          MAP4_WS1_REWO_BBOX_CE79,
          MAP5_WS2_REWE_BBOX_CE35,
          ]
     ),
    ({'headers': AUTHN_HEADERS_USER2,
      'workspace_type_list': [
          (None, None),
          (None, process_client.MAP_TYPE),
          (WS_USER2, process_client.MAP_TYPE),
      ],
      'rest_params': {},
      }, [LAY2_WS1_R2WO_BBOX_BC26,
          MAP1_WS1_REWE_BBOX_BF46,
          MAP2_WS1_REWE_BBOX_C3,
          MAP4_WS1_REWO_BBOX_CE79,
          MAP5_WS2_REWE_BBOX_CE35,
          MAP6_WS2_ROWO_BBOX_BD24,
          LAY1_WSP_REWE_BBOX_BC26,
          ]
     ),
    ({'headers': AUTHN_HEADERS_USER2,
      'workspace_type_list': [
          (None, None),
      ],
      'rest_params': {
          'order_by': 'bbox',
          'ordering_bbox': ','.join([f'{coord}' for coord in BBox.D4.value.epsg_3857]),
          'ordering_bbox_crs': crs_def.EPSG_3857,
          'bbox_filter': ','.join([f'{coord}' for coord in BBox.D4.value.epsg_3857]),
          'bbox_filter_crs': crs_def.EPSG_3857,
      },
      }, [MAP5_WS2_REWE_BBOX_CE35,
          MAP6_WS2_ROWO_BBOX_BD24,
          MAP1_WS1_REWE_BBOX_BF46,
          ]
     ),
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


def strip_accents(string):
    return ''.join(c for c in unicodedata.normalize('NFD', string) if unicodedata.category(c) != 'Mn')


def bbox_to_pylint_id_part(bbox, crs):
    epsg_code = crs.split(':')[-1]
    bbox_item = next(
        item for item in BBox
        if any(k for k, v in item.value.__dict__.items() if k == f"epsg_{epsg_code}" and v == bbox)
    )
    return f"{bbox_item.name}({epsg_code})"


def get_internal_pylint_id(query_params):
    pylint_id_parts = []
    if 'reader' in query_params:
        actor_name = 'reader'
        actor_value = query_params['reader']
    elif 'writer' in query_params:
        actor_name = 'writer'
        actor_value = query_params['writer']
    else:
        actor_name = 'actor'
        actor_value = 'admin'
    actor_value = 'anonym' if actor_value == settings.ANONYM_USER else actor_value
    pylint_id_parts.append((actor_name, actor_value))
    if 'full_text_filter' in query_params:
        pylint_id_parts.append(('full_text', f"'{strip_accents(query_params['full_text_filter'])}'"))
    if 'bbox_filter' in query_params:
        bbox_part = bbox_to_pylint_id_part(query_params['bbox_filter'],
                                           query_params['bbox_filter_crs'])
        pylint_id_parts.append(('bbox', bbox_part))
    if 'order_by_list' in query_params:
        assert len(query_params['order_by_list']) == 1
        order_by = query_params['order_by_list'][0]
        if order_by == 'full_text':
            pylint_id_parts.append(('order_by', f"'{strip_accents(query_params['ordering_full_text'])}'"))
        elif order_by == 'bbox':
            bbox_part = bbox_to_pylint_id_part(query_params['ordering_bbox'],
                                               query_params['ordering_bbox_crs'])
            pylint_id_parts.append(('order_by', f"bbox({bbox_part})"))
        elif order_by in ['title', 'last_change']:
            pylint_id_parts.append(('order_by', order_by.upper()))
    if 'limit' in query_params:
        pylint_id_parts.append(('limit', query_params['limit']))
    if 'offset' in query_params:
        pylint_id_parts.append(('offset', query_params['offset']))
    pytest_id = ' & '.join(f"{name}={value}" for name, value in pylint_id_parts)
    return pytest_id


def get_rest_pylint_id(query_params):
    pylint_id_parts = []
    headers = query_params['headers']
    if headers:
        actor_value = headers[process_client.TOKEN_HEADER][7:]
    else:
        actor_value = settings.ANONYM_USER
    pylint_id_parts.append(('user', actor_value))
    pylint_id_parts.append(('workspace', query_params.get('workspace')))
    publ_type = query_params.get('publ_type')
    pylint_id_parts.append(('type', publ_type.split('.')[1] if publ_type else publ_type))
    pytest_id = ' & '.join(f"{name}={value}" for name, value in pylint_id_parts)
    return pytest_id


def generate_test_cases(test_cases, *, pylint_id_generator=None):
    tc_list = []
    for idx, (query_params, exp_result) in enumerate(test_cases):
        if pylint_id_generator is not None:
            pytest_id = pylint_id_generator(query_params)
        else:
            pytest_id = f"query-{idx + 1}"
        test_case = base_test.TestCaseType(pytest_id=pytest_id,
                                           params={
                                               'query': query_params,
                                               'exp_result': exp_result,
                                           },
                                           type=EnumTestTypes.MANDATORY,
                                           )
        tc_list.append(test_case)
    return tc_list


def unpack_rest_test_case_query(query, expected):
    params = copy.deepcopy(query)
    unpacked = []
    ws_type_list = params.pop('workspace_type_list')
    for workspace, publ_type in ws_type_list:
        exp_list = [publication for publication in expected
                    if (publication.workspace == workspace or workspace is None)
                    and (publication.type == publ_type or publ_type is None)]
        unpacked.append((
            {
                **params,
                'workspace': workspace,
                'publ_type': publ_type,
            },
            {
                'items': exp_list,
                'total_count': len(exp_list),
                'content_range': (1, len(exp_list)),
            }
        ))
    assert len(unpacked) > 0
    return unpacked


@pytest.mark.usefixtures('ensure_layman_module', 'oauth2_provider_mock')
class TestGet:
    test_cases = {
        'test_internal_query': generate_test_cases(INTERNAL_TEST_CASES, pylint_id_generator=get_internal_pylint_id),
        'test_rest_query': generate_test_cases([(unpacked_query, unpacked_expected) for query, expected in REST_TEST_CASES for unpacked_query, unpacked_expected in unpack_rest_test_case_query(query, expected)], pylint_id_generator=get_rest_pylint_id),
    }

    usernames_to_reserve = USERNAMES

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
        headers = query_params.pop('headers')
        workspace = query_params.pop('workspace')
        publ_type = query_params.pop('publ_type')
        rest_params = query_params.pop('rest_params')

        exp_result = params['exp_result']

        method_args = {'workspace': workspace} if workspace else {}

        info_publications_response = process_client.get_publications_response(**{
            **{
                'publication_type': publ_type,
                'headers': headers,
                'query_params': rest_params,
            },
            **method_args,
        })

        info_publications_json = info_publications_response.json()
        info_publications = [Publication(item['workspace'], f'layman.{item["publication_type"]}', item['name'])
                             for item in info_publications_json]

        assert set(info_publications) == set(exp_result['items'])
        assert info_publications == exp_result['items']
        assert info_publications_response.headers['X-Total-Count'] == f"{exp_result['total_count']}"
        content_range_str = f"items {exp_result['content_range'][0]}-{exp_result['content_range'][1]}/{exp_result['total_count']}"
        assert info_publications_response.headers['Content-Range'] == content_range_str
