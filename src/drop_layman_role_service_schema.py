import psycopg2
import layman_settings as settings


def main():
    print(f"Drop Layman role service DB schema.")

    # Layman DB
    conn = psycopg2.connect(**settings.PG_CONN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f"""
DROP SCHEMA IF EXISTS "{settings.LAYMAN_INTERNAL_ROLE_SERVICE_SCHEMA}" CASCADE;
""")
    conn.commit()


if __name__ == "__main__":
    main()
