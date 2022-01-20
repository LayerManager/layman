from collections import namedtuple

CRSTypeDef = namedtuple('CRSTypeDef', [
    # Bounding box used if data file is empty (in EPSG:3857)
    'world_bbox',
    # If bounding box of layman.layer has no area in at least one dimension,
    # this padding in meters will be added to all dimensions whose coordinates equal
    # for GeoServer feature type definition and thumbnail rendering.
    # E.g. if bbox is [5, 100, 5, 200] and NO_AREA_BBOX_PADDING = 10,
    # thumbnail will be rendered with bbox [-5, 100, 15, 200].
    'no_area_bbox_padding',
    # Maximum coordinates of other CRS, which can be transformed
    'world_bounds',
    'qgis_template_spatialrefsys',
    # Boolean value, True if CRS definition in epsg.org DB specify axes in easting-northing order
    'axes_order_east_north_in_epsg_db',
    # Definition used for PostGIS spatial_ref_sys table
    'proj4text',
    # SRID of transformation definition if it differs from the default one
    'srid'
])

EPSG_3857 = 'EPSG:3857'
EPSG_4326 = 'EPSG:4326'
EPSG_5514 = 'EPSG:5514'

CRSDefinitions = {
    EPSG_3857: CRSTypeDef(
        world_bbox=(
            -20026376.39,
            -20048966.10,
            20026376.39,
            20048966.10,
        ),
        no_area_bbox_padding=10,
        world_bounds={
            EPSG_4326: (
                -180,
                -85.06,
                180,
                85.06,
            )
        },
        qgis_template_spatialrefsys='''<srsid>3857</srsid>
          <srid>3857</srid>
          <authid>EPSG:3857</authid>
          <description>WGS 84 / Pseudo-Mercator</description>
          <projectionacronym>merc</projectionacronym>
          <ellipsoidacronym>WGS84</ellipsoidacronym>
          <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=True,
        proj4text=None,
        srid=None,
    ),
    EPSG_4326: CRSTypeDef(
        world_bbox=(
            -180,
            -90,
            180,
            90,
        ),
        no_area_bbox_padding=0.00001,
        world_bounds=dict(),
        qgis_template_spatialrefsys='''<srsid>3452</srsid>
            <srid>4326</srid>
            <authid>EPSG:4326</authid>
            <description>WGS 84</description>
            <projectionacronym>longlat</projectionacronym>
            <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
            <geographicflag>true</geographicflag>''',
        axes_order_east_north_in_epsg_db=False,
        proj4text=None,
        srid=None,
    ),
    EPSG_5514: CRSTypeDef(
        world_bbox=(
            -951499.37,
            -1276279.09,
            -159365.31,
            -983013.08,
        ),
        no_area_bbox_padding=10,
        world_bounds=dict(),
        qgis_template_spatialrefsys='''<srsid>26812</srsid>
  <srid>5514</srid>
  <authid>EPSG:5514</authid>
  <description>S-JTSK / Krovak East North</description>
  <projectionacronym>krovak</projectionacronym>
  <ellipsoidacronym>EPSG:7004</ellipsoidacronym>
  <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=True,
        proj4text=None,
        srid=None,
    ),
}
