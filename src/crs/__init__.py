from collections import namedtuple

CRSTypeDef = namedtuple('CRSTypeDef', [
    # Bounding box used if data file is empty (in EPSG:3857)
    'world_bbox',
    # If bounding box of layman.layer has no area in at least one dimension,
    # this padding in meters will be added to all dimensions whose coordinates equal
    # for GeoServer feature type definition and thumbnail rendering.
    # E.g. if bbox is [5, 100, 5, 200] and NO_AREA_BBOX_PADDING = 10,
    # thumbnail will be rendered with bbox [-5, 100, 15, 200].
    'no_padding_area',
    # Maximum coordinates of other CRS, which can be transformed
    'world_bounds',
])

EPSG_3857 = 'EPSG:3857'
EPSG_4326 = 'EPSG:4326'

CRSDefinitions = {
    EPSG_3857: CRSTypeDef(
        world_bbox=(
            -20026376.39,
            -20048966.10,
            20026376.39,
            20048966.10,
        ),
        no_padding_area=10,
        world_bounds={
            EPSG_4326: (
                -180,
                -85.06,
                180,
                85.06,
            )
        }
    ),
    EPSG_4326: CRSTypeDef(
        world_bbox=(
            -180,
            -90,
            180,
            90,
        ),
        no_padding_area=0.00001,
        world_bounds=dict(),
    )
}
