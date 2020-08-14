import pytest

from .util import get_layman_users
from layman import settings


def test_layman_gs_user_not_in_get_usernames():
    usernames = get_layman_users()
    assert settings.LAYMAN_GS_USER not in usernames
