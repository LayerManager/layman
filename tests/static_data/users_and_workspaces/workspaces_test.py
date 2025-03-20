import pytest
from layman import app, util as layman_util
from ... import static_data as data
from ..data import ensure_all_publications


@pytest.mark.timeout(600)
@pytest.mark.parametrize('workspace', data.WORKSPACES)
@pytest.mark.usefixtures('oauth2_provider_mock', 'ensure_layman')
def test_user_workspace(workspace):
    ensure_all_publications()

    is_private_workspace = workspace in data.USERS

    all_sources = []
    for type_def in layman_util.get_publication_types(use_cache=False).values():
        all_sources += type_def['internal_sources']
    providers = layman_util.get_providers_from_source_names(all_sources)
    for provider in providers:
        with app.app_context():
            usernames = provider.get_usernames()
        if not is_private_workspace:
            assert workspace not in usernames, (workspace, provider)

    with app.app_context():
        usernames = layman_util.get_usernames(use_cache=False)
        workspaces = layman_util.get_workspaces()

    if is_private_workspace:
        assert workspace in usernames
    else:
        assert workspace not in usernames
    assert workspace in workspaces
