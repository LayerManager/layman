from test_tools import process_client

COMMON_WORKSPACE = 'test_workspace'

LAYER_TYPE = process_client.LAYER_TYPE
DEFINITION = 'definition'
TEST_DATA = 'test_data'


PUBLICATIONS = {
    (COMMON_WORKSPACE, LAYER_TYPE, 'post_jp2'): {
        DEFINITION: [
            {'file_paths': ['sample/layman.layer/sample_jp2_rgb.jp2', ]},
        ],
        TEST_DATA: {
            'bbox': (1829708, 6308828.600, 1833166.200, 6310848.600),
            'file_extensions': ['.jp2'],
            'normalized_color_interp': ['Red', 'Green', 'Blue'],
            'thumbnail': '/code/test_tools/data/thumbnail/raster_layer_jp2.png',
            'file_type': 'raster',
        },
    },
}

LIST_ALL_PUBLICATIONS = list(PUBLICATIONS.keys())
LIST_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication) in PUBLICATIONS
               if publ_type == LAYER_TYPE]
LIST_RASTER_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication), values in PUBLICATIONS.items()
                      if publ_type == LAYER_TYPE and values[TEST_DATA].get('file_type') == 'raster']
LIST_VECTOR_LAYERS = [(workspace, publ_type, publication) for (workspace, publ_type, publication), values in PUBLICATIONS.items()
                      if publ_type == LAYER_TYPE and values[TEST_DATA].get('file_type') == 'vector']
