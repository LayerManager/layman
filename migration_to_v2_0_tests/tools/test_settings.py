import layman_settings as settings

EXTERNAL_DB_NAME = 'external_test_db'

DB_URI = f"postgresql://{settings.LAYMAN_PG_USER}:{settings.LAYMAN_PG_PASSWORD}@localhost:25433/{settings.LAYMAN_PG_DBNAME}"

EXTERNAL_URI_STR = f'''postgresql://{settings.LAYMAN_PG_USER}:{settings.LAYMAN_PG_PASSWORD}@{settings.LAYMAN_PG_HOST}:{settings.LAYMAN_PG_PORT}/{EXTERNAL_DB_NAME}'''
