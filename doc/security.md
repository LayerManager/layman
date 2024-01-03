# Security

Layman`s security uses two well-known concepts:
- [authentication](#authentication)
- [authorization](#authorization)


## Authentication

Authentication (**authn**) is the process of obtaining and ensuring identity of [user](models.md#user) from incoming request to [REST API](rest.md).

Authentication is performed by chain of zero or more authentication modules controlled by [LAYMAN_AUTHN_MODULES](env-settings.md#LAYMAN_AUTHN_MODULES) environment variable. When request comes to REST API, security system calls authentication modules one by one (one module at a time), until one module ensures user identity or until there is no module left. If no module ensured user`s identity, user is considered as **anonymous** user.

Currently there is one optional authentication module:
- **OAuth2** module [`layman.authn.oauth2`](../src/layman/authn/oauth2), see separate [OAuth2 documentation](oauth2/index.md).

There is also one internal authentication module:
- **HTTP Header** module [`layman.authn.http_header`](../src/layman/authn/http_header). This module is required by Layman for internal purposes, so even if LAYMAN_AUTHN_MODULES does not contain `layman.authn.http_header` value, the value is appended automatically.

## Authorization

Authorization (**authz**) decides if authenticated [user](models.md#user) has permissions to perform the request to publication using [REST API](rest.md), [WMS](endpoints.md#web-map-service) and [WFS](endpoints.md#web-feature-service).

Authorization of **REST API** is performed by Layman itself. When authentication is finished, authorization module either allows request to be processed, raises an exception, or denies presence of requested publication. The behaviour depends on
- requested endpoint and action
- authenticated user
- [access rights of requested publication](#publication-access-rights)

Authorization of **WMS** and **WFS** is performed by Layman and GeoServer. On Layman, there are two important mechanisms:
- [synchronization of authorization-related data to GeoServer](data-storage.md#geoserver)
- Layman's authentication proxy that is placed in front of GeoServer's [WMS](endpoints.md#web-map-service) and [WFS](endpoints.md#web-feature-service) endpoints

Thanks to these mechanisms, GeoServer knows who is asking and if he can read/write requested layer.

### Publication Access Rights
Access rights enable user to control access to publications. Access to each publication is controlled by two access rights:
- **read**
   - grants `GET` HTTP requests to [single-publication REST API endpoints](#access-to-single-publication-endpoints)
   - grants presence of layer in response to `GET` HTTP requests in [multi-publication REST API endpoints](#access-to-multi-publication-endpoints)
   - grants presence of layer and its features in WMS and WFS responses 
- **write**
   - grants `POST`, `PATCH`, and `DELETE` HTTP requests to [single-publication REST API endpoints](#access-to-single-publication-endpoints)
   - grants deleting the publication by `DELETE` HTTP request to [multi-publication REST API endpoints](#access-to-multi-publication-endpoints)
   - grants WFS-T requests to the layer

Both read and write access rights contain list of [usernames](models.md#username) or [role names](models.md#role).

Users listed in access rights, either directly or indirectly through roles, are granted to perform described actions.

Access rights are set by [POST Workspace Layers](rest.md#post-workspace-layers) request and can be changed by [PATCH Workspace Layer](rest.md#patch-workspace-layer) request (analogically for maps). 

#### Access to single-publication endpoints
Single-publication endpoints are:
- [Layer](rest.md#overview) and nested endpoints 
- [Map](rest.md#overview) and nested endpoints 

Access to these endpoints is completely controlled by [access rights](#publication-access-rights). 

#### Access to multi-publication endpoints
Multi-publication endpoints are:
- [Layers](rest.md#overview) 
- [Maps](rest.md#overview) 

Access is treated by following rules:
- Every authenticated user can send [POST Workspace Layers](rest.md#post-workspace-layers) to his own [personal workspace](models.md#personal-workspace).
- Everyone can send [POST Workspace Layers](rest.md#post-workspace-layers) to any existing [public workspace](models.md#public-workspace) if and only if she is listed in [GRANT_PUBLISH_IN_PUBLIC_WORKSPACE](env-settings.md#GRANT_PUBLISH_IN_PUBLIC_WORKSPACE) (directly or through role).
- Everyone can send [POST Workspace Layers](rest.md#post-workspace-layers) to any not-yet-existing [public workspace](models.md#public-workspace) if and only if she is listed in [GRANT_CREATE_PUBLIC_WORKSPACE](env-settings.md#GRANT_CREATE_PUBLIC_WORKSPACE) (directly or through role). Such action leads to creation of the public workspace.
- Everyone can send [GET Workspace Layers](rest.md#get-workspace-layers) request to any workspace, receiving only publications she has read access to.
- Everyone can send [DELETE Workspace Layers](rest.md#delete-workspace-layers) request to any workspace, deleting only publications she has write access to.

It's analogical for maps.

### Role Service
Despite of [usernames](models.md#username), [role names](models.md#role) are not controlled by Layman, but by **role service**.

Role service can be any PostgreSQL DB schema containing table (or view, or materialized view) structure described in [GeoServer documentation](https://docs.geoserver.org/2.21.x/en/user/security/usergrouprole/roleservices.html#jdbc-role-service). Furthermore, Layman has special requirements to records in the tables. There are two types of records: [admin records](#admin-role-service-records) and [business records](#business-role-service-records). No other records are allowed.

Role service is used by both Layman and GeoServer when [access rights](#publication-access-rights) are evaluated.

Role service is identified by [LAYMAN_ROLE_SERVICE_URI](env-settings.md#LAYMAN_ROLE_SERVICE_URI). It can contain URI to any PostgreSQL schema that meets mentioned requirements, e.g. to [internal role service schema](#internal-role-service-schema).

#### Admin role-service records

Admin records are needed for Layman and GeoServer to handle authorization correctly.

- Table `roles` must contain records

| name                                                                | parent |
|---------------------------------------------------------------------|--------|
| `ADMIN`                                                             | null   |
| `GROUP_ADMIN`                                                       | null   |
| value of [LAYMAN_GS_ROLE](./env-settings.md#LAYMAN_GS_ROLE)         | null   |
| `USER_<username>` of every user with [username](models.md#username) | null   |

These records do not appear in [GET Roles](rest.md#get-roles). They are also not accepted in access rights.

- Table `user_roles` must contain records

| username                                                                                         | rolename |
|--------------------------------------------------------------------------------------------------|----------|
| `admin`                                                                                          | `ADMIN`  |
| value of [LAYMAN_GS_USER](./env-settings.md#LAYMAN_GS_USER)                                      | `ADMIN`  |
| value of [LAYMAN_GS_USER](./env-settings.md#LAYMAN_GS_USER)                                      | value of [LAYMAN_GS_ROLE](./env-settings.md#LAYMAN_GS_ROLE) |
| every [username](models.md#username)| `USER_<username>` |
| every [username](models.md#username)| value of [LAYMAN_GS_ROLE](./env-settings.md#LAYMAN_GS_ROLE) |

#### Business role-service records

Table `roles` may contain other records that appear in [GET Roles](rest.md#get-roles) and are accepted in access rights. Their `name` must match to regular expression `[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*` and `parent` must be null. Names `ROLE_ADMINISTRATOR`, `ROLE_GROUP_ADMIN`, `ROLE_AUTHENTICATED`, `ROLE_ANONYMOUS`, and `EVERYONE` are forbidden.

Table `user_roles` may contain other records that connects [users](models.md#user) with [roles](#role-service).

#### Internal Role Service Schema
Layman provides PostgreSQL DB schema `_role_service` that can be used as the role service. The schema contain all necessary [admin records](#admin-role-service-records) and (by default) no [business records](#business-role-service-records). Business records can be added manually to tables `bussiness_roles` and `bussiness_user_roles`.
