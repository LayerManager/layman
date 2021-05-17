import re
import requests
import pytest

from layman import settings


@pytest.mark.parametrize("method", [
    requests.get,
    requests.post,
    requests.put,
    requests.patch,
    requests.delete,
])
@pytest.mark.parametrize("path", [
    '/rest/{workspace}/layers',
    '/rest/{workspace}/layers/{publication}',
    '/rest/{workspace}/layers/{publication}/chunk',
    '/rest/{workspace}/layers/{publication}/metadata-comparison',
    '/rest/{workspace}/layers/{publication}/style',
    '/rest/{workspace}/layers/{publication}/thumbnail',
    '/rest/{workspace}/maps',
    '/rest/{workspace}/maps/{publication}',
    '/rest/{workspace}/maps/{publication}/file',
    '/rest/{workspace}/maps/{publication}/metadata-comparison',
    '/rest/{workspace}/maps/{publication}/thumbnail',
])
@pytest.mark.usefixtures('ensure_layman')
def test_deprecated_header(method,
                           path):
    depr_headers = ['Deprecation', 'Link']
    workspace = 'test_deprecated_header_workspace'
    publication = 'test_deprecated_header_publication'
    url = f'http://{settings.LAYMAN_SERVER_NAME}' + path.format(workspace=workspace, publication=publication)
    response = method(url)
    if response.status_code == 405:
        return
    assert all(header in response.headers.keys() for header in depr_headers), (response.headers, response.status_code, response.text)

    link_header = response.headers['Link']
    alternate_link = re.search('<(.+?)>;', link_header).group(1)

    url_new = url.replace('/rest/', f'/rest/{settings.REST_WORKSPACES_PREFIX}/')
    assert alternate_link == url_new, link_header
    response = method(url_new)
    assert all(header not in response.headers.keys() for header in depr_headers), (response.headers, response.status_code, response.text)
