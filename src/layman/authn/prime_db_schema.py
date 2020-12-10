from layman.common.prime_db_schema import ensure_whole_user


def save_username_reservation(username, iss_id, sub, claims):
    userinfo = {"issuer_id": iss_id,
                "sub": sub,
                "claims": claims,
                }
    ensure_whole_user(username, userinfo)
