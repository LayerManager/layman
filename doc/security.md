# Security

Layman`s security uses two well-known concepts:
- [authentication](#authentication)
- [authorization](#authorization)


## Authentication

Authentication (**authn**) is the process of obtaining and ensuring identity of [user](models.md#user) from incoming request to [REST API](rest.md).

Authentication is performed by chain of zero or more authentication modules controlled by [LAYMAN_AUTHN_MODULES](env-settings.md#LAYMAN_AUTHN_MODULES) environment variable. When request comes to REST API, security system calls authentication modules one by one (one module at a time), until one module ensures user identity or until there is no module left. If no module ensured user`s identity, user is considered as **anonymous** user.

Currently there is one optional authentication module:
- **OAuth2** module [`layman.authn.oauth2`](../src/layman/authn/oauth2) with Liferay as authorization server. See separate [OAuth2 documentation](oauth2/index.md).

There is also one internal authentication module:
- **HTTP Header** module [`layman.authn.http_header`](../src/layman/authn/http_header). This module is required by Layman for internal purposes, so even if LAYMAN_AUTHN_MODULES does not contain `layman.authn.http_header` value, the value is appended automatically.

## Authorization

Authorization (**authz**) decides if authenticated [user](models.md#user) has permissions to perform the request to [REST API](rest.md).

Authorization is performed by single authorization module. When authentication is finished, security system calls authorization module that either passes or raises an exception.

### Access to single-publication endpoints
Access to single-publication REST API endpoints is configurable by users. These endpoints are:
- [Layer](rest.md#overview) and nested endpoints 
- [Map](rest.md#overview) and nested endpoints 

To control access to these endpoints, authorization module uses so called **access rights**. There are following types of access rights:
- **read**: grants `GET` HTTP requests
- **write**: grants `POST`, `PUT`, `PATCH`, and `DELETE` HTTP requests

Both read and write access rights contain list of user names or roles. Currently, Layman accepts following roles:
- EVERYONE: every user including anonymous

Users listed in access rights, either directly or indirectly through roles, are granted to perform related HTTP actions.

Access rights are set by [POST Layers](rest.md#post-layers) request and can be changed by [PATCH Layer](rest.md#patch-layer) request (analogically for maps). 

### Access to multi-publication endpoints
Access to **multi-publication REST API endpoints**, e.g. [Layers](rest.md#overview) and [Maps](rest.md#overview), is treated by following rules:
- Everyone can send [GET Layers](rest.md#get-layers) request to any workspace, receiving only publications he has read access to.
- Every authenticated user can send [POST Layers](rest.md#post-layers) to his own [personal workspace](models.md#personal-workspace).
- Everyone can send [POST Layers](rest.md#post-layers) to any [public workspace](models.md#public-workspace) if and only if he is listed in [GRANT_PUBLISH_IN_PUBLIC_WORKSPACE](env-settings.md#GRANT_PUBLISH_IN_PUBLIC_WORKSPACE) (directly or through role). Furthermore, automatic creation of not-yet-existing [public workspace](models.md#public-workspace) on [POST Layers](rest.md#post-layers) is controlled by [GRANT_CREATE_PUBLIC_WORKSPACE](env-settings.md#GRANT_CREATE_PUBLIC_WORKSPACE).
- Everyone can send [DELETE Layers](rest.md#delete-layers) request to any workspace, deleting only publications she has write access to.

It's analogical for maps.

