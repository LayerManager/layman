ERROR_LIST = {
    1: (400, 'Missing parameter'),
    2: (400, 'Wrong parameter value'),
    3: (409, 'File already exists'),
    4: (400, 'Unsupported CRS of data file'),
    5: (400, 'Data file does not contain single layer'),
    6: (500, 'Cannot connect to database'),
    7: (500, 'Database query error'),
    # 8: (409, 'Reserved DB schema name'),
    9: (409, 'DB object already exists'),
    # 10: (409, 'DB schema owned by another than layman user'),
    11: (500, 'Error during import data into DB'),
    # 12: (409, 'GeoServer workspace not assigned to LAYMAN_GS_ROLE'),
    # 13: (409, 'Reserved GeoServer workspace name'),
    # 14: (400, 'Invalid SLD file'), -- Separated to Geoserver module
    15: (404, 'Layer was not found'),
    16: (404, 'Thumbnail was not found'),
    17: (409, 'Layer already exists'),
    18: (400, 'Missing one or more ShapeFile files.'),
    # 19: (400, 'Layer is already in process.'),
    20: (400, 'Chunk upload is not active for this layer.'),
    21: (400, 'Unknown combination of resumableFilename and '
              'layman_original_parameter.'),
    22: (400, 'UPLOAD_MAX_INACTIVITY_TIME during upload reached.'),
    23: (409, 'Publication already exists.'),
    24: (409, 'Map already exists'),
    25: (404, 'This endpoint and method are not implemented yet!'),
    26: (404, 'Map was not found'),
    27: (404, 'File was not found'),
    28: (400,
         'Zero-length identifier found. Data file probably contains attribute with zero-length name (e.g. empty string).'),
    # 29: (400, 'Map is already in process.'),
    30: (403, 'Unauthorized access'),
    31: (400, 'Unexpected HTTP method.'),
    32: (403, 'Unsuccessful OAuth2 authentication.'),
    33: (400, 'Authenticated user did not claim any username within Layman yet.'),
    34: (400, 'User already reserved username.'),
    35: (409, 'Workspace name already reserved.'),
    36: (409, 'Metadata record already exists.'),
    37: (400, 'CSW exception.'),
    38: (400, 'Micka HTTP or connection error.'),
    39: (404, 'Metadata record does not exists.'),
    40: (404, 'Workspace does not exist.'),
    41: (409, 'Username is in conflict with LAYMAN_GS_USER. To resolve this conflict, you can create new GeoServer user with another name to become new LAYMAN_GS_USER, give him LAYMAN_GS_ROLE and ADMIN roles, remove the old LAYMAN_GS_USER user at GeoServer, change environment settings LAYMAN_GS_USER and LAYMAN_GS_PASSWORD, and restart Layman'),
    42: (409, 'LAYMAN_PRIME_SCHEMA is in conflict with existing workspace name.'),
    43: (400, 'Wrong access rights.'),
    44: (403, 'Unsuccessful HTTP Header authentication.'),
    45: (400, 'Workspace ended with reserved suffix.'),
    46: (400, 'Unknown style file. Can recognize only SLD and QML files.'),
    47: (400, 'Error in QML'),
    48: (400, 'Wrong combination of parameters'),
    49: (400, 'Publication is already in process.'),
    50: (500, 'Error when normalizing raster file'),
    51: (500, 'Error when generating thumbnail'),
    52: (400, 'Too many style files'),
}
