import logging
import os
import pathlib
import re
import requests

from . import util

logger = logging.getLogger(__name__)

DEFAULT_CONNECTION_TIMEOUT = int(os.environ['DEFAULT_CONNECTION_TIMEOUT'])
EPSG_ENCODING = 'iso-8859-1'

EPSG_PROPERTIES_DEFAULT = {
    3034: '3034=PROJCS["ETRS89 / LCC Europe",GEOGCS["ETRS89",DATUM["European_Terrestrial_Reference_System_1989",'
          'SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6258"]],'
          'PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],'
          'AUTHORITY["EPSG","4258"]],PROJECTION["Lambert_Conformal_Conic_2SP"],PARAMETER["standard_parallel_1",35],'
          'PARAMETER["standard_parallel_2",65],PARAMETER["latitude_of_origin",52],PARAMETER["central_meridian",10],'
          'PARAMETER["false_easting",4000000],PARAMETER["false_northing",2800000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],'
          'AUTHORITY["EPSG","3034"]]',
    3035: '3035=PROJCS["ETRS89 / LAEA Europe",GEOGCS["ETRS89",DATUM["European_Terrestrial_Reference_System_1989",'
          'SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6258"]],'
          'PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],'
          'AUTHORITY["EPSG","4258"]],PROJECTION["Lambert_Azimuthal_Equal_Area"],PARAMETER["latitude_of_center",52],'
          'PARAMETER["longitude_of_center",10],PARAMETER["false_easting",4321000],PARAMETER["false_northing",3210000],'
          'UNIT["metre",1,AUTHORITY["EPSG","9001"]],AUTHORITY["EPSG","3035"]]',
    3059: '3059=PROJCS["LKS92 / Latvia TM",GEOGCS["LKS92",DATUM["Latvia_1992",SPHEROID["GRS 1980",6378137,298.257222101,'
          'AUTHORITY["EPSG","7019"]],TOWGS84[0,0,0,0,0,0,0],AUTHORITY["EPSG","6661"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],'
          'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4661"]],PROJECTION["Transverse_Mercator"],'
          'PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",24],PARAMETER["scale_factor",0.9996],'
          'PARAMETER["false_easting",500000],PARAMETER["false_northing",-6000000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],'
          'AUTHORITY["EPSG","3059"]]',
    3857: '3857=PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,'
          'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",'
          '0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],'
          'PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],'
          'UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 '
          '+lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs"],AUTHORITY["EPSG","3857"]]',
    4326: '4326=GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG",'
          '"6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],'
          'AUTHORITY["EPSG","4326"]]',
    5514: '5514=PROJCS["S-JTSK / Krovak East North",GEOGCS["S-JTSK",DATUM["System Jednotne Trigonometricke Site Katastralni",'
          'SPHEROID["Bessel 1841",6377397.155,299.1528128,AUTHORITY["EPSG","7004"]],TOWGS84[572.213,85.334,461.94,4.9732,-1.529,'
          '-5.2484,3.5378],AUTHORITY["EPSG","6156"]],PRIMEM["Greenwich",0.0,AUTHORITY["EPSG","8901"]],UNIT["degree",'
          '0.017453292519943295],AXIS["Geodetic longitude",EAST],AXIS["Geodetic latitude", NORTH],AUTHORITY["EPSG","4156"]],'
          'PROJECTION["Krovak",AUTHORITY["EPSG","9819"]],PARAMETER["latitude_of_center",49.5],PARAMETER["longitude_of_center",'
          '24.833333333333332],PARAMETER["azimuth", 30.288139722222223],PARAMETER["pseudo_standard_parallel_1",78.5],'
          'PARAMETER["scale_factor",0.9999],PARAMETER["false_easting",0.0],PARAMETER["false_northing",0.0],UNIT["m", 1.0],AXIS["X",'
          'EAST],AXIS["Y",NORTH],AUTHORITY["EPSG","5514"]]',
    32634: '32634=PROJCS["WGS 84 / UTM zone 34N",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,'
           'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",'
           '0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],'
           'PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",21],PARAMETER["scale_factor",0.9996],'
           'PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",'
           'EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","32634"]]',
    32633: '32633=PROJCS["WGS 84 / UTM zone 33N",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,'
           'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",'
           '0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],'
           'PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",15],PARAMETER["scale_factor",0.9996],'
           'PARAMETER["false_easting",500000],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",'
           'EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","32633"]]',
    102067: '102067=PROJCS["S-JTSK_Krovak_East_North",GEOGCS["GCS_S_JTSK",DATUM["Jednotne_Trigonometricke_Site_Katastralni",'
            'SPHEROID["Bessel_1841",6377397.155,299.1528128]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]],'
            'PROJECTION["Krovak"],PARAMETER["False_Easting",0],PARAMETER["False_Northing",0],PARAMETER["Pseudo_Standard_Parallel_1",'
            '78.5],PARAMETER["Scale_Factor",0.9999],PARAMETER["Azimuth",30.28813975277778],PARAMETER["Longitude_Of_Center",'
            '24.83333333333333],PARAMETER["Latitude_Of_Center",49.5],PARAMETER["X_Scale",-1],PARAMETER["Y_Scale",1],'
            'PARAMETER["XY_Plane_Rotation",90],UNIT["Meter",1],AUTHORITY["EPSG","102067"]]',
    32718: '32718=PROJCS["WGS 84 / UTM zone 18S",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,'
           'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",'
           '0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Transverse_Mercator"],'
           'PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-75],PARAMETER["scale_factor",0.9996],'
           'PARAMETER["false_easting",500000],PARAMETER["false_northing",10000000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],'
           'AXIS["Easting",EAST],AXIS["Northing",NORTH],AUTHORITY["EPSG","32718"]]',
    9377: '9377=PROJCS["MAGNA-SIRGAS 2018 / Origen-Nacional",GEOGCS["MAGNA-SIRGAS 2018",DATUM["Marco_Geocentrico_Nacional_de_Referencia_2018",'
          'SPHEROID["GRS 1980",6378137,298.257222101],TOWGS84[0,0,0,0,0,0,0]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],'
          'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","20046"]],PROJECTION["Transverse_Mercator"],'
          'PARAMETER["latitude_of_origin",4],PARAMETER["central_meridian",-73],PARAMETER["scale_factor",0.9992],'
          'PARAMETER["false_easting",5000000],PARAMETER["false_northing",2000000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],'
          'AUTHORITY["EPSG","9377"]]',
}


def get_epsg_codes_from_epsg_file(file_path):
    result = set()
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding=EPSG_ENCODING) as file:
            epsg_props = file.read()
        epsg_defs = re.finditer(r'^([1-9][0-9]+)=', epsg_props, re.MULTILINE)
        result = {int(epsg_def.group(1)) for epsg_def in epsg_defs}
    return result


def setup_epsg(data_dir, srs_list):

    file_name = 'epsg.properties'
    srs_list = {util.get_epsg_code(crs) for crs in srs_list}

    file_path = os.path.join(data_dir, 'user_projections', file_name)
    pathlib.Path(os.path.dirname(file_path)).mkdir(parents=True, exist_ok=True)
    old_epsg_codes = get_epsg_codes_from_epsg_file(file_path)
    missing_srs = srs_list.difference(old_epsg_codes)
    new_epsg = {code: definition for code, definition in EPSG_PROPERTIES_DEFAULT.items()
                if code in missing_srs}

    srs_to_download = missing_srs.difference(new_epsg.keys())
    if new_epsg or srs_to_download:
        logger.info(f"Ensuring GeoServer EPSG definition for SRS list: '{srs_list}'")
        logger.info(f"  already in {file_name}: {old_epsg_codes}")
        logger.info(f"  found in Layman internal definition: {set(new_epsg.keys())}")
        logger.info(f"  to download from epsg.io: {srs_to_download}")
    else:
        logger.info(f"No change in GeoServer EPSG definition for SRS list: '{srs_list}'")
    for code in srs_to_download:
        try:
            url = f'http://epsg.io/{code}.geoserver'
            res = requests.get(url,
                               timeout=DEFAULT_CONNECTION_TIMEOUT)
            res.raise_for_status()
            new_epsg[code] = res.text
        except BaseException as ex:
            logger.warning(f'Not able to download EPSG definition from epsg.io for code={code}. Reason={ex}')

    with open(file_path, "a", encoding=EPSG_ENCODING) as file:
        for epsg_definition in new_epsg.values():
            file.write(epsg_definition)
            file.write('\n')
