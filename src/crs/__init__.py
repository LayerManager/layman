from collections import namedtuple

CRSTypeDef = namedtuple('CRSTypeDef', [
    # Bounding box used if data file is empty (in EPSG:3857)
    'default_bbox',
    # Maximum bounding box used to crop calculated bbox
    'max_bbox',
    # If bounding box of layman.layer has no area in at least one dimension,
    # this padding in meters will be added to all dimensions whose coordinates equal
    # for GeoServer feature type definition and thumbnail rendering.
    # E.g. if bbox is [5, 100, 5, 200] and NO_AREA_BBOX_PADDING = 10,
    # thumbnail will be rendered with bbox [-5, 100, 15, 200].
    'no_area_bbox_padding',
    # Maximum coordinates of other CRS, which can be transformed by DB
    'world_bounds',
    'qgis_template_spatialrefsys',
    # Boolean value, True if CRS definition in epsg.org DB specify axes in easting-northing order
    'axes_order_east_north_in_epsg_db',
    # Definition used for PostGIS spatial_ref_sys table
    # It is used when transforming bounding boxes in prime DB schema.
    # It is not used for data transformation in WMS and WFS (data are transformed by GeoServer or QGIS).
    'proj4text',
    # SRID of transformation definition if it differs from the default one
    # Relevant only for internal DB, not for external DBs.
    'internal_srid'
])

EPSG_3857 = 'EPSG:3857'
EPSG_4326 = 'EPSG:4326'
CRS_84 = 'CRS:84'
EPSG_5514 = 'EPSG:5514'
EPSG_32633 = 'EPSG:32633'
EPSG_32634 = 'EPSG:32634'
EPSG_3034 = 'EPSG:3034'
EPSG_3035 = 'EPSG:3035'
EPSG_3059 = 'EPSG:3059'

CRSDefinitions = {
    EPSG_3857: CRSTypeDef(
        default_bbox=(
            -20026376.39,
            -20048966.10,
            20026376.39,
            20048966.10,
        ),
        max_bbox=(
            -20026376.39,
            -20048966.10,
            20026376.39,
            20048966.10,
        ),
        no_area_bbox_padding=10,
        world_bounds={
            EPSG_4326: (
                -179.9,
                -85.06,
                179.9,
                85.06,
            )
        },
        qgis_template_spatialrefsys='''<wkt>PROJCRS["WGS 84 / Pseudo-Mercator",BASEGEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble",MEMBER["World Geodetic System 1984 (Transit)"],MEMBER["World Geodetic System 1984 (G730)"],MEMBER["World Geodetic System 1984 (G873)"],MEMBER["World Geodetic System 1984 (G1150)"],MEMBER["World Geodetic System 1984 (G1674)"],MEMBER["World Geodetic System 1984 (G1762)"],MEMBER["World Geodetic System 1984 (G2139)"],ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[2.0]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4326]],CONVERSION["Popular Visualisation Pseudo-Mercator",METHOD["Popular Visualisation Pseudo Mercator",ID["EPSG",1024]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["easting (X)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["northing (Y)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Web mapping and visualisation."],AREA["World between 85.06°S and 85.06°N."],BBOX[-85.06,-180,85.06,180]],ID["EPSG",3857]]</wkt>
      <proj4>+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs</proj4>
      <srsid>3857</srsid>
      <srid>3857</srid>
      <authid>EPSG:3857</authid>
      <description>WGS 84 / Pseudo-Mercator</description>
      <projectionacronym>merc</projectionacronym>
      <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
      <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=True,
        proj4text=None,
        internal_srid=None,
    ),
    EPSG_4326: CRSTypeDef(
        default_bbox=(
            -180,
            -90,
            180,
            90,
        ),
        max_bbox=(
            -180,
            -90,
            180,
            90,
        ),
        no_area_bbox_padding=0.00001,
        world_bounds={},
        qgis_template_spatialrefsys='''<wkt>GEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble",MEMBER["World Geodetic System 1984 (Transit)"],MEMBER["World Geodetic System 1984 (G730)"],MEMBER["World Geodetic System 1984 (G873)"],MEMBER["World Geodetic System 1984 (G1150)"],MEMBER["World Geodetic System 1984 (G1674)"],MEMBER["World Geodetic System 1984 (G1762)"],MEMBER["World Geodetic System 1984 (G2139)"],ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[2.0]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],CS[ellipsoidal,2],AXIS["geodetic latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],AXIS["geodetic longitude (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]],USAGE[SCOPE["Horizontal component of 3D system."],AREA["World."],BBOX[-90,-180,90,180]],ID["EPSG",4326]]</wkt>
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
        internal_srid=None,
    ),
    EPSG_5514: CRSTypeDef(
        default_bbox=(
            -951499.37,
            -1276279.09,
            -159365.31,
            -983013.08,
        ),
        max_bbox=None,
        no_area_bbox_padding=10,
        world_bounds={},
        qgis_template_spatialrefsys='''<wkt>PROJCRS["S-JTSK / Krovak East North",BASEGEOGCRS["S-JTSK",DATUM["System of the Unified Trigonometrical Cadastral Network",ELLIPSOID["Bessel 1841",6377397.155,299.1528128,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4156]],CONVERSION["Krovak East North (Greenwich)",METHOD["Krovak (North Orientated)",ID["EPSG",1041]],PARAMETER["Latitude of projection centre",49.5,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8811]],PARAMETER["Longitude of origin",24.8333333333333,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8833]],PARAMETER["Co-latitude of cone axis",30.2881397527778,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",1036]],PARAMETER["Latitude of pseudo standard parallel",78.5,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8818]],PARAMETER["Scale factor on pseudo standard parallel",0.9999,SCALEUNIT["unity",1],ID["EPSG",8819]],PARAMETER["False easting",0,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["easting (X)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["northing (Y)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["GIS."],AREA["Czechia; Slovakia."],BBOX[47.73,12.09,51.06,22.56]],ID["EPSG",5514]]</wkt>
      <proj4>+proj=krovak +lat_0=49.5 +lon_0=24.8333333333333 +alpha=30.2881397527778 +k=0.9999 +x_0=0 +y_0=0 +ellps=bessel +towgs84=589,76,480,0,0,0,0 +units=m +no_defs</proj4>
      <srsid>26812</srsid>
      <srid>5514</srid>
      <authid>EPSG:5514</authid>
      <description>S-JTSK / Krovak East North</description>
      <projectionacronym>krovak</projectionacronym>
      <ellipsoidacronym>EPSG:7004</ellipsoidacronym>
      <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=True,
        proj4text=None,
        internal_srid=None,
    ),
    EPSG_32633: CRSTypeDef(
        default_bbox=(
            166021.44,
            0.00,
            1004994.66,
            9329005.18,
        ),
        max_bbox=None,
        no_area_bbox_padding=1,
        world_bounds={},
        qgis_template_spatialrefsys='''<wkt>PROJCRS["WGS 84 / UTM zone 33N",BASEGEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble",MEMBER["World Geodetic System 1984 (Transit)"],MEMBER["World Geodetic System 1984 (G730)"],MEMBER["World Geodetic System 1984 (G873)"],MEMBER["World Geodetic System 1984 (G1150)"],MEMBER["World Geodetic System 1984 (G1674)"],MEMBER["World Geodetic System 1984 (G1762)"],MEMBER["World Geodetic System 1984 (G2139)"],ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[2.0]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4326]],CONVERSION["UTM zone 33N",METHOD["Transverse Mercator",ID["EPSG",9807]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",15,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["Scale factor at natural origin",0.9996,SCALEUNIT["unity",1],ID["EPSG",8805]],PARAMETER["False easting",500000,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["(E)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["(N)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Engineering survey, topographic mapping."],AREA["Between 12°E and 18°E, northern hemisphere between equator and 84°N, onshore and offshore. Austria. Bosnia and Herzegovina. Cameroon. Central African Republic. Chad. Congo. Croatia. Czechia. Democratic Republic of the Congo (Zaire). Gabon. Germany. Hungary. Italy. Libya. Malta. Niger. Nigeria. Norway. Poland. San Marino. Slovakia. Slovenia. Svalbard. Sweden. Vatican City State."],BBOX[0,12,84,18]],ID["EPSG",32633]]</wkt>
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
        internal_srid=None,
    ),
    EPSG_32634: CRSTypeDef(
        default_bbox=(
            166021.44,
            0.00,
            534994.66,
            9329005.18,
        ),
        max_bbox=None,
        no_area_bbox_padding=1,
        world_bounds={},
        qgis_template_spatialrefsys='''<wkt>PROJCRS["WGS 84 / UTM zone 34N",BASEGEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble",MEMBER["World Geodetic System 1984 (Transit)"],MEMBER["World Geodetic System 1984 (G730)"],MEMBER["World Geodetic System 1984 (G873)"],MEMBER["World Geodetic System 1984 (G1150)"],MEMBER["World Geodetic System 1984 (G1674)"],MEMBER["World Geodetic System 1984 (G1762)"],MEMBER["World Geodetic System 1984 (G2139)"],ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[2.0]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4326]],CONVERSION["UTM zone 34N",METHOD["Transverse Mercator",ID["EPSG",9807]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",21,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["Scale factor at natural origin",0.9996,SCALEUNIT["unity",1],ID["EPSG",8805]],PARAMETER["False easting",500000,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",0,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["(E)",east,ORDER[1],LENGTHUNIT["metre",1]],AXIS["(N)",north,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Engineering survey, topographic mapping."],AREA["Between 18°E and 24°E, northern hemisphere between equator and 84°N, onshore and offshore. Albania. Belarus. Bosnia and Herzegovina. Bulgaria. Central African Republic. Chad. Croatia. Democratic Republic of the Congo (Zaire). Estonia. Finland. Greece. Hungary. Italy. Kosovo. Latvia. Libya. Lithuania. Montenegro. North Macedonia. Norway, including Svalbard and Bjornoys. Poland. Romania. Russian Federation. Serbia. Slovakia. Sudan. Sweden. Ukraine."],BBOX[0,18,84,24]],ID["EPSG",32634]]</wkt>
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
        internal_srid=None,
    ),
    EPSG_3034: CRSTypeDef(
        default_bbox=(
            1584884.54,
            1150546.94,
            8442721.99,
            6678398.53,
        ),
        max_bbox=None,
        no_area_bbox_padding=1,
        world_bounds={
            EPSG_4326: (
                -180,
                -89.99999,
                180,
                89.99999,
            )
        },
        qgis_template_spatialrefsys='''<wkt>PROJCRS["ETRS89-extended / LCC Europe",BASEGEOGCRS["ETRS89",ENSEMBLE["European Terrestrial Reference System 1989 ensemble",MEMBER["European Terrestrial Reference Frame 1989"],MEMBER["European Terrestrial Reference Frame 1990"],MEMBER["European Terrestrial Reference Frame 1991"],MEMBER["European Terrestrial Reference Frame 1992"],MEMBER["European Terrestrial Reference Frame 1993"],MEMBER["European Terrestrial Reference Frame 1994"],MEMBER["European Terrestrial Reference Frame 1996"],MEMBER["European Terrestrial Reference Frame 1997"],MEMBER["European Terrestrial Reference Frame 2000"],MEMBER["European Terrestrial Reference Frame 2005"],MEMBER["European Terrestrial Reference Frame 2014"],ELLIPSOID["GRS 1980",6378137,298.257222101,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[0.1]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4258]],CONVERSION["Europe Conformal 2001",METHOD["Lambert Conic Conformal (2SP)",ID["EPSG",9802]],PARAMETER["Latitude of false origin",52,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8821]],PARAMETER["Longitude of false origin",10,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8822]],PARAMETER["Latitude of 1st standard parallel",35,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8823]],PARAMETER["Latitude of 2nd standard parallel",65,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8824]],PARAMETER["Easting at false origin",4000000,LENGTHUNIT["metre",1],ID["EPSG",8826]],PARAMETER["Northing at false origin",2800000,LENGTHUNIT["metre",1],ID["EPSG",8827]]],CS[Cartesian,2],AXIS["northing (N)",north,ORDER[1],LENGTHUNIT["metre",1]],AXIS["easting (E)",east,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Conformal mapping at scales of 1:500,000 and smaller."],AREA["Europe - European Union (EU) countries and candidates. Europe - onshore and offshore: Albania; Andorra; Austria; Belgium; Bosnia and Herzegovina; Bulgaria; Croatia; Cyprus; Czechia; Denmark; Estonia; Faroe Islands; Finland; France; Germany; Gibraltar; Greece; Hungary; Iceland; Ireland; Italy; Kosovo; Latvia; Liechtenstein; Lithuania; Luxembourg; Malta; Monaco; Montenegro; Netherlands; North Macedonia; Norway including Svalbard and Jan Mayen; Poland; Portugal including Madeira and Azores; Romania; San Marino; Serbia; Slovakia; Slovenia; Spain including Canary Islands; Sweden; Switzerland; Türkiye (Turkey); United Kingdom (UK) including Channel Islands and Isle of Man; Vatican City State."],BBOX[24.6,-35.58,84.73,44.83]],ID["EPSG",3034]]</wkt>
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
        internal_srid=900915,
    ),
    EPSG_3035: CRSTypeDef(
        default_bbox=(
            1896628.62,
            1507846.05,
            4662111.45,
            6829874.45,
        ),
        max_bbox=None,
        no_area_bbox_padding=1,
        world_bounds={},
        qgis_template_spatialrefsys='''<wkt>PROJCRS["ETRS89-extended / LAEA Europe",BASEGEOGCRS["ETRS89",ENSEMBLE["European Terrestrial Reference System 1989 ensemble",MEMBER["European Terrestrial Reference Frame 1989"],MEMBER["European Terrestrial Reference Frame 1990"],MEMBER["European Terrestrial Reference Frame 1991"],MEMBER["European Terrestrial Reference Frame 1992"],MEMBER["European Terrestrial Reference Frame 1993"],MEMBER["European Terrestrial Reference Frame 1994"],MEMBER["European Terrestrial Reference Frame 1996"],MEMBER["European Terrestrial Reference Frame 1997"],MEMBER["European Terrestrial Reference Frame 2000"],MEMBER["European Terrestrial Reference Frame 2005"],MEMBER["European Terrestrial Reference Frame 2014"],ELLIPSOID["GRS 1980",6378137,298.257222101,LENGTHUNIT["metre",1]],ENSEMBLEACCURACY[0.1]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4258]],CONVERSION["Europe Equal Area 2001",METHOD["Lambert Azimuthal Equal Area",ID["EPSG",9820]],PARAMETER["Latitude of natural origin",52,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",10,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["False easting",4321000,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",3210000,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["northing (Y)",north,ORDER[1],LENGTHUNIT["metre",1]],AXIS["easting (X)",east,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Statistical analysis."],AREA["Europe - European Union (EU) countries and candidates. Europe - onshore and offshore: Albania; Andorra; Austria; Belgium; Bosnia and Herzegovina; Bulgaria; Croatia; Cyprus; Czechia; Denmark; Estonia; Faroe Islands; Finland; France; Germany; Gibraltar; Greece; Hungary; Iceland; Ireland; Italy; Kosovo; Latvia; Liechtenstein; Lithuania; Luxembourg; Malta; Monaco; Montenegro; Netherlands; North Macedonia; Norway including Svalbard and Jan Mayen; Poland; Portugal including Madeira and Azores; Romania; San Marino; Serbia; Slovakia; Slovenia; Spain including Canary Islands; Sweden; Switzerland; Türkiye (Turkey); United Kingdom (UK) including Channel Islands and Isle of Man; Vatican City State."],BBOX[24.6,-35.58,84.73,44.83]],ID["EPSG",3035]]</wkt>
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
        internal_srid=900916,
    ),
    EPSG_3059: CRSTypeDef(
        default_bbox=(
            189423.14,
            180420.28,
            749893.19,
            446584.80,
        ),
        max_bbox=None,
        no_area_bbox_padding=1,
        world_bounds={},
        qgis_template_spatialrefsys='''<wkt>PROJCRS["LKS92 / Latvia TM",BASEGEOGCRS["LKS92",DATUM["Latvia 1992",ELLIPSOID["GRS 1980",6378137,298.257222101,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],ID["EPSG",4661]],CONVERSION["Latvian Transverse Mercator",METHOD["Transverse Mercator",ID["EPSG",9807]],PARAMETER["Latitude of natural origin",0,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8801]],PARAMETER["Longitude of natural origin",24,ANGLEUNIT["degree",0.0174532925199433],ID["EPSG",8802]],PARAMETER["Scale factor at natural origin",0.9996,SCALEUNIT["unity",1],ID["EPSG",8805]],PARAMETER["False easting",500000,LENGTHUNIT["metre",1],ID["EPSG",8806]],PARAMETER["False northing",-6000000,LENGTHUNIT["metre",1],ID["EPSG",8807]]],CS[Cartesian,2],AXIS["northing (X)",north,ORDER[1],LENGTHUNIT["metre",1]],AXIS["easting (Y)",east,ORDER[2],LENGTHUNIT["metre",1]],USAGE[SCOPE["Engineering survey, topographic mapping."],AREA["Latvia - onshore and offshore."],BBOX[55.67,19.06,58.09,28.24]],ID["EPSG",3059]]</wkt>
      <proj4>+proj=tmerc +lat_0=0 +lon_0=24 +k=0.9996 +x_0=500000 +y_0=-6000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs</proj4>
      <srsid>1022</srsid>
      <srid>3059</srid>
      <authid>EPSG:3059</authid>
      <description>LKS92 / Latvia TM</description>
      <projectionacronym>tmerc</projectionacronym>
      <ellipsoidacronym>EPSG:7019</ellipsoidacronym>
      <geographicflag>false</geographicflag>''',
        axes_order_east_north_in_epsg_db=False,
        proj4text='+proj=tmerc +lat_0=0 +lon_0=24 +k=0.9996 +x_0=500000 +y_0=-6000000 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs',
        internal_srid=900917,
    ),
}


CRS_URN = {
    CRS_84: 'urn:ogc:def:crs:OGC:1.3:CRS84',
}
