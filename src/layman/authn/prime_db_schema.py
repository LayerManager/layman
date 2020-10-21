from layman.common.prime_db_schema import users


def save_username_reservation(username, iss_id, sub, claims):
    userinfo = {"iss_id": iss_id,
                "sub": sub,
                "claims": claims,
                }
    users.ensure_user(username, userinfo)
