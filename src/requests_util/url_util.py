from urllib import parse


def redact_uri(uri, *, remove_username=False):
    url_components = parse.urlparse(uri)
    if url_components.username or url_components.password:
        hostname = f'{url_components.hostname}:{url_components.port}' if url_components.port else url_components.hostname
        url_components = url_components._replace(
            netloc=f"{url_components.username}@{hostname}" if not remove_username else f"{hostname}",
        )

    return url_components.geturl()
