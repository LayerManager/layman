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
EPSG_32633 = 'EPSG:32633'
EPSG_32634 = 'EPSG:32634'
EPSG_3034 = 'EPSG:3034'
EPSG_3035 = 'EPSG:3035'

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
        qgis_template_spatialrefsys='''<wkt>PROJCS["S-JTSK / Krovak East North",GEOGCS["S-JTSK",DATUM["System_Jednotne_Trigonometricke_Site_Katastralni",SPHEROID["Bessel 1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],TOWGS84[570.8,85.7,462.8,4.998,1.587,5.261,3.56],AUTHORITY["EPSG","6156"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4156"]],PROJECTION["Krovak"],PARAMETER["latitude_of_center",49.5],PARAMETER["longitude_of_center",24.83333333333333],PARAMETER["azimuth",30.28813972222222],PARAMETER["pseudo_standard_parallel_1",78.5],PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","5514"]]</wkt>
  <proj4>+proj=krovak +lat_0=49.5 +lon_0=24.83333333333333 +alpha=30.28813972222222 +k=0.9999 +x_0=0 +y_0=0 +ellps=bessel +towgs84=570.8,85.7,462.8,4.998,1.587,5.261,3.56 +units=m +no_defs</proj4>
  <srsid>26812</srsid>
  <srid>900914</srid>
  <authid>EPSG:5514</authid>
  <description>S-JTSK / Krovak East North</description>
  <projectionacronym>krovak</projectionacronym>
  <ellipsoidacronym>EPSG:7004</ellipsoidacronym>
  <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=True,
        proj4text='+proj=krovak +lat_0=49.5 +lon_0=24.83333333333333 +alpha=30.28813972222222 +k=0.9999 +x_0=0 +y_0=0 +ellps=bessel +towgs84=570.8,85.7,462.8,4.998,1.587,5.261,3.56 +units=m +no_defs',
        srid=900914,
    ),
    EPSG_32633: CRSTypeDef(
        world_bbox=(
            166021.44,
            0.00,
            1004994.66,
            9329005.18,
        ),
        no_area_bbox_padding=1,
        world_bounds=dict(),
        qgis_template_spatialrefsys='''<wkt>PROJCRS["WGS 84 / UTM zone 33N",BASEGEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4326]],CONVERSION["UTM zone 33N",METHOD["Transverse Mercator",ID["EPSG",9807]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",15,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["Scale factor at natural origin",0.9996,SCALEUNIT["unity",1],ID["EPSG",8805]],PARAMETER["False easting",500000,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["(E)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["(N)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["unknown"],AREA["World - N hemisphere - 12°E to 18°E - by country"],BBOX[0,12,84,18]],ID["EPSG",32633]]</wkt>
      <proj4>+proj=utm +zone=33 +datum=WGS84 +units=m +no_defs</proj4>
      <srsid>3117</srsid>
      <srid>32633</srid>
      <authid>EPSG:32633</authid>
      <description>WGS 84 / UTM zone 33N</description>
      <projectionacronym>utm</projectionacronym>
      <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
      <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=True,
        proj4text=None,
        srid=None,
    ),
    EPSG_32634: CRSTypeDef(
        world_bbox=(
            6021.44,
            0.00,
            1004994.66,
            9329005.18,
        ),
        no_area_bbox_padding=1,
        world_bounds=dict(),
        qgis_template_spatialrefsys='''<wkt>PROJCRS["WGS 84 / UTM zone 34N",BASEGEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4326]],CONVERSION["UTM zone 34N",METHOD["Transverse Mercator",ID["EPSG",9807]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",21,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["Scale factor at natural origin",0.9996,SCALEUNIT["unity",1],ID["EPSG",8805]],PARAMETER["False easting",500000,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["(E)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["(N)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["unknown"],AREA["World - N hemisphere - 18°E to 24°E - by country"],BBOX[0,18,84,24]],ID["EPSG",32634]]</wkt>
      <proj4>+proj=utm +zone=34 +datum=WGS84 +units=m +no_defs</proj4>
      <srsid>3118</srsid>
      <srid>32634</srid>
      <authid>EPSG:32634</authid>
      <description>WGS 84 / UTM zone 34N</description>
      <projectionacronym>utm</projectionacronym>
      <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
      <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=True,
        proj4text=None,
        srid=None,
    ),
    EPSG_3034: CRSTypeDef(
        world_bbox=(
            1584884.54,
            1150546.94,
            8442721.99,
            6678398.53,
        ),
        no_area_bbox_padding=1,
        world_bounds=dict(),
        qgis_template_spatialrefsys='''<wkt>PROJCRS["ETRS89-extended / LCC Europe",BASEGEOGCRS["ETRS89",DATUM["European Terrestrial Reference System 1989",ELLIPSOID["GRS 1980",6378137,298.257222101,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4258]],CONVERSION["Europe Conformal 2001",METHOD["Lambert Conic Conformal (2SP)",ID["EPSG",9802]],PARAMETER["Latitude of false origin",52,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8821]],PARAMETER["Longitude of false origin",10,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8822]],PARAMETER["Latitude of 1st standard parallel",35,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8823]],PARAMETER["Latitude of 2nd standard parallel",65,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8824]],PARAMETER["Easting at false origin",4000000,LENGTHUNIT["metre",1],ID["EPSG",8826]],PARAMETER["Northing at false origin",2800000,LENGTHUNIT["metre",1],ID["EPSG",8827]]],CS[Cartesian,2],AXIS["northing (N)",north,ORDER[1],LENGTHUNIT["metre",1]],AXIS["easting (E)",east,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["unknown"],AREA["Europe - LCC &amp; LAEA"],BBOX[24.6,-35.58,84.17,44.83]],ID["EPSG",3034]]</wkt>
      <proj4>+proj=lcc +lat_0=52 +lon_0=10 +lat_1=35 +lat_2=65 +x_0=4000000 +y_0=2800000 +ellps=GRS80 +units=m +no_defs</proj4>
      <srsid>999</srsid>
      <srid>3034</srid>
      <authid>EPSG:3034</authid>
      <description>ETRS89-extended / LCC Europe</description>
      <projectionacronym>lcc</projectionacronym>
      <ellipsoidacronym>EPSG:7019</ellipsoidacronym>
      <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=False,
        proj4text='+proj=lcc +lat_1=35 +lat_2=65 +lat_0=52 +lon_0=10 +x_0=4000000 +y_0=2800000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs ',
        srid=90015,
    ),
    EPSG_3035: CRSTypeDef(
        world_bbox=(
            1584884.54,
            1507846.05,
            8442721.99,
            6829874.45,
        ),
        no_area_bbox_padding=1,
        world_bounds=dict(),
        qgis_template_spatialrefsys='''<wkt>PROJCRS["ETRS89-extended / LAEA Europe",BASEGEOGCRS["ETRS89",DATUM["European Terrestrial Reference System 1989",ELLIPSOID["GRS 1980",6378137,298.257222101,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4258]],CONVERSION["Europe Equal Area 2001",METHOD["Lambert Azimuthal Equal Area",ID["EPSG",9820]],PARAMETER["Latitude of natural origin",52,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",10,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",4321000,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",3210000,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["northing (Y)",north,ORDER[1],LENGTHUNIT["metre",1]],AXIS["easting (X)",east,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["unknown"],AREA["Europe - LCC &amp; LAEA"],BBOX[24.6,-35.58,84.17,44.83]],ID["EPSG",3035]]</wkt>
      <proj4>+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +units=m +no_defs</proj4>
      <srsid>1000</srsid>
      <srid>3035</srid>
      <authid>EPSG:3035</authid>
      <description>ETRS89-extended / LAEA Europe</description>
      <projectionacronym>laea</projectionacronym>
      <ellipsoidacronym>EPSG:7019</ellipsoidacronym>
      <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=False,
        proj4text='+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs ',
        srid=90016,
    ),
}
