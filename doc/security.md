# Security

Layman`s security uses two well-known concepts:
- [authentication](#authentication)
- [authorization](#authorization)


## Authentication

Authentication (**authn**) is the process of obtaining and ensuring identity of user from incoming request to [REST API](rest.md).

Authentication is performed by chain of zero or more authentication modules controlled by [`AUTHN_MODULES`](../src/layman_settings.py) setting. When request comes to REST API, security system calls authentication modules one by one (one module at a time), until one module ensures user identity or until there is no module left. If no module ensured user`s identity, user is considered as **anonymous** user.

Currently there are two authentication options:
- use no authentication module, so every user is considered as **anonymous**
- **OAuth2** module ([`'layman.authn.oauth2'`](../src/layman/authn/oauth2)) with Liferay as authorization server. See separate [OAuth2 documentation](oauth2/index.md).

## Authorization

Authorization (**authz**) decides if authenticated user has permissions to perform the request to [REST API](rest.md).

Authorization is performed by single authorization module controlled by [`AUTHZ_MODULE`](../src/layman_settings.py) setting. When authentication is finished, security system calls authorization module that either passes or raises an exception "Unauthorised access" returned as HTTP Error 403.

There are two types of operations used in permissions:
- **read**: includes all `GET` requests
- **write**: includes all `POST`, `PUT`, `PATCH`, `DELETE` requests

Currently there are two authorization modules implemented:

| name | description |
| --- | --- |
| [read everyone, write everyone](../src/layman/authz/read_everyone_write_everyone.py) | everyone including anonymous user is able to **read** and **write** to anybody`s workspace |
| [read everyone, write owner](../src/layman/authz/read_everyone_write_owner.py) | everyone including anonymous user is able to **read** anybody`s workspace, but only owner of the workspace is able to **write** |

