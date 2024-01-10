import os
import layman_settings as settings
from db import util as db_util


def main():
    assert settings.OAUTH2_INTROSPECTION_SUB_KEY == 'userId', f"OAUTH2_INTROSPECTION_SUB_KEY is expected to be `userId`"
    assert settings.OAUTH2_INTROSPECTION_USE_SUB_KEY_FROM_USER_PROFILE is True, f"OAUTH2_INTROSPECTION_USE_SUB_KEY_FROM_USER_PROFILE is expected to be `true`"

    wagtail_db_uri = os.getenv('LAYMAN_WAGTAIL_DB_URI', None)
    assert wagtail_db_uri is not None, f"LAYMAN_WAGTAIL_DB_URI must be set"

    wagtail_user_rows = db_util.run_query(f"select id, username from auth_user;", uri_str=wagtail_db_uri)
    assert len(set(r[0] for r in wagtail_user_rows)) == len(wagtail_user_rows), f"Wagtail userIds are expected to be unique"
    assert len(set(r[1] for r in wagtail_user_rows)) == len(wagtail_user_rows), f"Wagtail usernames are expected to be unique"
    wagtail_username_to_id = {
        username: f"{user_id}"
        for user_id, username in wagtail_user_rows
    }

    layman_user_rows = db_util.run_query(f"""
select u.id, u.issuer_id, u.sub, w.name as username
from {settings.LAYMAN_PRIME_SCHEMA}.users u
  inner join {settings.LAYMAN_PRIME_SCHEMA}.workspaces w on u.id_workspace = w.id
    """, uri_str=settings.PG_URI_STR)

    print(f"Found {len(wagtail_user_rows)} Wagtail users:")
    for user_id, username in wagtail_user_rows:
        print(f"  {username}, id={user_id}")

    print(f"Found {len(layman_user_rows)} Layman users with username registered.")
    print(f'Processing Layman users ...')

    changed_subs = 0
    for layman_user_id, issuer_id, sub, username in layman_user_rows:
        print(f"  {username} (id={layman_user_id}, sub={sub}, issuer_id={issuer_id})")
        if issuer_id != 'layman.authn.oauth2':
            print(f"    WARNING: User has unexpected issuer_id, skipping.")
            continue
        new_sub = wagtail_username_to_id.get(sub)
        if new_sub is None:
            print(f"    WARNING: Sub of the user was not found among Wagtail usernames, skipping.")
            continue
        print(f'    Changing sub from `{sub}` to `{new_sub}`')
        db_util.run_statement(
            f"UPDATE {settings.LAYMAN_PRIME_SCHEMA}.users set sub = %s where id = %s",
            data=(new_sub, layman_user_id), uri_str=settings.PG_URI_STR)
        changed_subs += 1
        print(f'      Changed!')
    print(f'Processing finished, changed {changed_subs} OAuth2 subs of {len(layman_user_rows)} Layman users.')


if __name__ == '__main__':
    main()
