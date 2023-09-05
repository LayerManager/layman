# Layman behind client proxy

It is common use case that Layman is queried not directly, but using **client proxy**. The client proxy reads session cookie from the request, substitutes the cookie for authentication header, sends the request to the Layman, and returns result to user agent. This approach is used in Layman Test Client and HSLayers client, and it is mentioned also in [OAuth2 documentation](oauth2/index.md#request-layman-rest-api).

The client proxy used with Layman always adds prefix to URL path of each request. Without client proxy, URL path of request to [REST API](rest.md) looks like `/rest/path/to/endpoint`. When client proxy is used, the URL path changes to `/<client-proxy-prefix>/rest/path/to/endpoint`.

Imagine request e.g. to [GET Publications](rest.md#get-publications) sent through client proxy, e.g. `/layman-client-proxy`. URL path of such request sent by user agent will be `/layman-client-proxy/rest/publications` and the response will look like

```json
[
  {
    "workspace": "my_workspace",
    "publication_type": "layer",
    "name": "my_layer",
    "url": "https://mylaymandomain.com/rest/publications",
    ...
  },
  ...
]
```

By default, Layman will not adjust URLs in its response to contain also URL path prefix of the client proxy (`/layman-proxy` in above example). If you prefer to adjust URLs in Layman responses to contain also URL path prefix of the client proxy, you need to send also `X-Forwarded-Prefix` HTTP header with the request.

## X-Forwarded-Prefix HTTP header

The value of the `X-Forwarded-Prefix` HTTP header will be used as prefix in some URL paths of Layman response.

For example, if you send request to `/layman-client-proxy/rest/publications` with HTTP header `X-Forwarded-Prefix=/layman-client-proxy` then response will change to

```json
[
  {
    "workspace": "my_workspace",
    "publication_type": "layer",
    "name": "my_layer",
    "url": "https://mylaymandomain.com/layman-client-proxy/rest/publications",
    ...
  },
  ...
]
```

Currently, value of `X-Forwarded-Prefix` affects following URLs:
* [GET Publications](rest.md#get-publications)
  * `url` key
* [GET Layers](rest.md#get-layers)
  * `url` key
* [GET Workspace Layers](rest.md#get-workspace-layers)
  * `url` key
* [GET Maps](rest.md#get-maps)
  * `url` key
* [GET Workspace Maps](rest.md#get-workspace-maps)
  * `url` key
* [GET Workspace Layer](rest.md#get-workspace-layer)
  * `url` key
  * `wms`.`url` key
  * `wfs`.`url` key
  * `style`.`url` key
  * `thumbnail`.`url` key
  * `metadata`.`comparison_url` key
* [GET Workspace Map](rest.md#get-workspace-map)
  * `url` key
  * `file`.`url` key
  * `thumbnail`.`url` key
  * `metadata`.`comparison_url` key
* [POST Workspace Layers](rest.md#post-workspace-layers)
  * `url` key
* [DELETE Workspace Layer](rest.md#delete-workspace-layer)
  * `url` key
* [DELETE Workspace Layers](rest.md#delete-workspace-layers)
  * `url` key
* [DELETE Workspace Map](rest.md#delete-workspace-map)
  * `url` key
* [DELETE Workspace Maps](rest.md#delete-workspace-maps)
  * `url` key
* [POST Workspace Maps](rest.md#post-workspace-maps)
  * `url` key
