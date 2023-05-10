from urllib import parse
from dataclasses import dataclass


@dataclass
class TableUri:
    def __init__(self, *, db_uri_str, schema, table, geo_column, primary_key_column):
        self.db_uri_str = db_uri_str
        self.schema = schema
        self.table = table
        self.geo_column = geo_column
        self.primary_key_column = primary_key_column

    _db_uri_str: str
    _db_uri: parse.ParseResult
    schema: str
    table: str
    geo_column: str

    @property
    def db_uri_str(self):
        return self._db_uri_str

    @db_uri_str.setter
    def db_uri_str(self, value):
        self._db_uri_str = value
        self._db_uri = parse.urlparse(value) if value else None

    @property
    def hostname(self):
        return self._db_uri.hostname if self._db_uri else None

    @property
    def port(self):
        return self._db_uri.port if self._db_uri else None

    @property
    def db_name(self):
        return self._db_uri.path[1:] if self._db_uri else None

    @property
    def username(self):
        return parse.unquote(self._db_uri.username) if self._db_uri else None

    @property
    def password(self):
        return parse.unquote(self._db_uri.password) if self._db_uri else None


PG_URI_STR = str()
