import pytest

import crs as crs_def
from layman import settings, app as app
from layman.common.prime_db_schema import publications
from layman.layer import LAYER_TYPE
from test_tools import prime_db_schema_client, process_client


@pytest.mark.usefixtures('ensure_layman_module')
class TestWorldBboxFilter:
    workspace = 'test_world_bbox_filter_workspace'
    layer_prefix = 'test_world_bbox_filter_layer'

    @pytest.fixture(scope="class")
    def provide_data(self):
        for crs, values in crs_def.CRSDefinitions.items():
            layer = self.layer_prefix + '_' + crs.split(':')[1]
            prime_db_schema_client.post_workspace_publication(LAYER_TYPE, self.workspace, layer,
                                                              geodata_type=settings.GEODATA_TYPE_VECTOR,
                                                              wfs_wms_status=settings.EnumWfsWmsStatus.AVAILABLE.value,
                                                              )
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
            process_client.get_publications(publication_type=None,
                                            query_params={
                                                'bbox_filter': '-100,-100,100,100',
                                                'bbox_filter_crs': crs,
                                            })

    @staticmethod
    @pytest.mark.parametrize('crs', crs_def.CRSDefinitions.keys())
    @pytest.mark.usefixtures('provide_data')
    def test_world_bbox_ordering(crs):
        with app.app_context():
            publications.get_publication_infos_with_metainfo(ordering_bbox=(-100, -100, 100, 100),
                                                             ordering_bbox_crs=crs,
                                                             order_by_list=['bbox', ])
            process_client.get_publications(publication_type=None,
                                            query_params={
                                                'order_by': 'bbox',
                                                'ordering_bbox': '-100,-100,100,100',
                                                'ordering_bbox_crs': crs,
                                            })
