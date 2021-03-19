from . import get_usernames
from layman import settings


def test_layman_gs_user_not_in_get_usernames():
    usernames = get_usernames()
    assert settings.LAYMAN_GS_USER not in usernames
