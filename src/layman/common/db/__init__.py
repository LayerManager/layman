import re


def launder_attribute_name(attr_name):
    # https://github.com/OSGeo/gdal/blob/355b41831cd2685c85d1aabe5b95665a2c6e99b7/gdal/ogr/ogrsf_frmts/pgdump/ogrpgdumpdatasource.cpp#L129,L155
    # lower case only 26 English letters, not other letters, in the same way as ogr2ogr
    lower_name = re.sub(r'([A-Z]+)', lambda match: match.group(1).lower(), attr_name)
    return re.sub(r"['\-#]", '_', lower_name)
