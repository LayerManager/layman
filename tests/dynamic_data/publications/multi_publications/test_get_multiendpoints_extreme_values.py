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


class TestExtremeCoordinatesFilter:
    # pylint: disable=too-few-public-methods

    workspace = 'test_extreme_coordinates_filter'
    name_prefix = 'test_extreme_coordinates_filter_publication'
    publ_type = LAYER_TYPE

    @pytest.mark.parametrize('layer_suffix, x_coord_idx, y_coord_idx', [
        ('min_corner', 0, 1,),
        ('max_corner', 2, 3,),
    ])
    @pytest.mark.parametrize('crs, crs_values', crs_def.CRSDefinitions.items())
    def test_default_bbox_corner_filter(self, crs, crs_values, layer_suffix, x_coord_idx, y_coord_idx):
        name = self.name_prefix + '_' + crs.split(':')[1] + '_' + layer_suffix
        prime_db_schema_client.post_workspace_publication(self.publ_type, self.workspace, name,
                                                          geodata_type=settings.GEODATA_TYPE_VECTOR,
                                                          wfs_wms_status=settings.EnumWfsWmsStatus.AVAILABLE.value,
                                                          )
        default_bbox = crs_values.default_bbox
        point_bbox = (
            default_bbox[x_coord_idx],
            default_bbox[y_coord_idx],
            default_bbox[x_coord_idx],
            default_bbox[y_coord_idx]
        )
        with app.app_context():
            publications.set_bbox(self.workspace, LAYER_TYPE, name, point_bbox, crs)

            publication_infos = publications.get_publication_infos(workspace_name=self.workspace,
                                                                   pub_type=self.publ_type,
                                                                   )
        info = publication_infos[(self.workspace, self.publ_type, name)]
        native_bbox = info['native_bounding_box']
        native_crs = info['native_crs']

        bbox_3857 = info['bounding_box']
        crs_3857 = crs_def.EPSG_3857

        assert native_bbox == list(point_bbox)
        assert native_crs == crs

        with app.app_context():
            publication_infos = publications.get_publication_infos_with_metainfo(workspace_name=self.workspace,
                                                                                 pub_type=self.publ_type,
                                                                                 bbox_filter=tuple(native_bbox),
                                                                                 bbox_filter_crs=native_crs,
                                                                                 )
        assert (self.workspace, self.publ_type, name) in publication_infos['items']

        publication_infos = process_client.get_publications(publication_type=self.publ_type,
                                                            workspace=self.workspace,
                                                            query_params={
                                                                'bbox_filter': ','.join(str(c) for c in native_bbox),
                                                                'bbox_filter_crs': native_crs,
                                                            })
        assert (self.workspace, self.publ_type, name) in [
            (publication['workspace'], f'layman.{publication["publication_type"]}', publication['name']) for publication in
            publication_infos]

        with app.app_context():
            publication_infos = publications.get_publication_infos_with_metainfo(workspace_name=self.workspace,
                                                                                 pub_type=self.publ_type,
                                                                                 bbox_filter=tuple(bbox_3857),
                                                                                 bbox_filter_crs=crs_3857,
                                                                                 )
        assert (self.workspace, self.publ_type, name) in publication_infos['items']

        publication_infos = process_client.get_publications(publication_type=self.publ_type,
                                                            workspace=self.workspace,
                                                            query_params={
                                                                'bbox_filter': ','.join(str(c) for c in bbox_3857),
                                                                'bbox_filter_crs': crs_3857,
                                                            })
        assert (self.workspace, self.publ_type, name) in [
            (publication['workspace'], f'layman.{publication["publication_type"]}', publication['name']) for publication in
            publication_infos]

        with app.app_context():
            publications.delete_publication(self.workspace, self.publ_type, name,)
