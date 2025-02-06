import layman_settings as settings

DB_URI = f"postgresql://{settings.LAYMAN_PG_USER}:{settings.LAYMAN_PG_PASSWORD}@localhost:25433/{settings.LAYMAN_PG_DBNAME}"
