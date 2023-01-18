from dataclasses import dataclass


@dataclass
class TableUri:
    db_uri_str: str
    schema: str
    table: str
    geo_column: str


# It's expected to be set from another module
# Example:
# PG_CONN = {
#     'host': LAYMAN_PG_HOST,
#     'port': LAYMAN_PG_PORT,
#     'dbname': LAYMAN_PG_DBNAME,
#     'user': LAYMAN_PG_USER,
#     'password': LAYMAN_PG_PASSWORD,
# }
PG_CONN = {}
