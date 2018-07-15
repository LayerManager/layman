ERROR_LIST = {
    1: (400, 'Missing parameter'),
    2: (400, 'Wrong parameter value'),
    3: (409, 'File already exists'),
    4: (400, 'Unsupported CRS of data file'),
    5: (400, 'Data file does not contain single layer'),
    6: (500, 'Cannot connect to database'),
    7: (500, 'Database query error'),
    8: (409, 'Reserved DB schema name'),
    9: (409, 'DB object already exists'),
    10: (409, 'DB schema owned by another than layman user'),
}