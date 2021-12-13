from collections import namedtuple

CRSTypeDef = namedtuple('CRSTypeDef', [
    # Bounding box used if data file is empty (in EPSG:3857)
    'world_bbox',
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
    ),
    EPSG_4326: CRSTypeDef(
        world_bbox=(
            -180,
            -90,
            180,
            90,
        ),
    )
}
