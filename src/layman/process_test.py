import pytest

from test import process

ensure_layman = process.ensure_layman


@pytest.mark.usefixtures('ensure_layman')
def test_normal_layman():
    pass


@pytest.mark.usefixtures('ensure_layman')
def test_normal_layman1():
    pass


def test_special_layman():
    env_vars = dict(process.AUTHN_SETTINGS)
    env_vars['GRANT_CREATE_PUBLIC_WORKSPACE'] = ''
    env_vars['GRANT_PUBLISH_IN_PUBLIC_WORKSPACE'] = ''
    process.ensure_layman_function(env_vars)


def test_special_layman2():
    env_vars = dict(process.AUTHN_SETTINGS)
    env_vars['GRANT_CREATE_PUBLIC_WORKSPACE'] = ''
    env_vars['GRANT_PUBLISH_IN_PUBLIC_WORKSPACE'] = ''
    process.ensure_layman_function(env_vars)


@pytest.mark.usefixtures('ensure_layman')
def test_normal_layman2():
    pass
