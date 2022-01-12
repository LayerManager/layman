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
        qgis_template_spatialrefsys='''<wkt>PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs"],AUTHORITY["EPSG","3857"]]</wkt>
          <proj4>+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs</proj4>
          <srsid>3857</srsid>
          <srid>3857</srid>
          <authid>EPSG:3857</authid>
          <description>WGS 84 / Pseudo-Mercator</description>
          <projectionacronym>merc</projectionacronym>
          <ellipsoidacronym>WGS84</ellipsoidacronym>
          <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=True,
        proj4text=None,
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
        qgis_template_spatialrefsys='''<wkt>GEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS
                84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],CS[ellipsoidal,2],AXIS["geodetic
                latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],AXIS["geodetic longitude
                (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]],USAGE[SCOPE["unknown"],AREA["World"],BBOX[-90,-180,90,180]],ID["EPSG",4326]]
            </wkt>
            <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
            <srsid>3452</srsid>
            <srid>4326</srid>
            <authid>EPSG:4326</authid>
            <description>WGS 84</description>
            <projectionacronym>longlat</projectionacronym>
            <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
            <geographicflag>true</geographicflag>''',
        axes_order_east_north_in_epsg_db=False,
        proj4text=None,
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
        qgis_template_spatialrefsys='''<wkt>PROJCRS["S-JTSK / Krovak East North",BASEGEOGCRS["S-JTSK",DATUM["System of the Unified Trigonometrical Cadastral Network",ELLIPSOID["Bessel 1841",6377397.155,299.1528128,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4156]],CONVERSION["Krovak East North (Greenwich)",METHOD["Krovak (North Orientated)",ID["EPSG",1041]],PARAMETER["Latitude of projection centre",49.5,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8811]],PARAMETER["Longitude of origin",24.8333333333333,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8833]],PARAMETER["Co-latitude of cone axis",30.2881397527778,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",1036]],PARAMETER["Latitude of pseudo standard parallel",78.5,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8818]],PARAMETER["Scale factor on pseudo standard parallel",0.9999,SCALEUNIT["unity",1],ID["EPSG",8819]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["easting (X)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["northing (Y)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["unknown"],AREA["Europe - Czechoslovakia"],BBOX[47.73,12.09,51.06,22.56]],ID["EPSG",5514]]</wkt>
  <proj4>+proj=krovak +lat_0=49.5 +lon_0=24.83333333333333 +alpha=30.28813972222222 +k=0.9999 +x_0=0 +y_0=0 +ellps=bessel +towgs84=572.213,85.334,461.94,-4.9732,-1.529,-5.2484,3.5378 +units=m +no_defs</proj4>
  <srsid>26812</srsid>
  <srid>5514</srid>
  <authid>EPSG:5514</authid>
  <description>S-JTSK / Krovak East North</description>
  <projectionacronym>krovak</projectionacronym>
  <ellipsoidacronym>EPSG:7004</ellipsoidacronym>
  <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=True,
        proj4text='+proj=krovak +lat_0=49.5 +lon_0=24.83333333333333 +alpha=30.28813972222222 +k=0.9999 +x_0=0 +y_0=0 +ellps=bessel +towgs84=572.213,85.334,461.94,-4.9732,-1.529,-5.2484,3.5378 +units=m +no_defs ',
    ),
}
