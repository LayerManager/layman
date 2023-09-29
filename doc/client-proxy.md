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

By default, Layman will not adjust URLs in its response to contain also URL path prefix of the client proxy (`/layman-proxy` in above example). If you prefer to adjust URLs in Layman responses to contain also URL path prefix of the client proxy (or even host and protocol), you need to send also [X-Forwarded HTTP headers](#x-forwarded-http-headers) with the request.

## X-Forwarded HTTP headers

Layman supports three optional X-Forwarded HTTP headers, whose values will be used in some URLs in Layman responses:
- `X-Forwarded-Proto`: The value will be used as protocol in some URLs, and it is required to be `http` or `https`.
- `X-Forwarded-Host`: The value will be used as host in some URLs, and it is required to match regular expression `^(?=.{1,253}\.?(?:\:[0-9]{1,5})?$)(?:(?!-)[a-z0-9-_]{1,63}(?<!-)(?:\.|(?:\:[0-9]{1,5})?$))+$`.
- `X-Forwarded-Prefix`: The value will be used as prefix in some URL paths, and it is required to match regular expression `^(?:/[a-z0-9_-]+)*$`.

For example, consider there is layman running at `https://enjoychallenge.tech/rest` and client proxy running at `https://laymanproxy.com/layman-client-proxy`. If you send request to your Layman proxy `https://laymanproxy.com/layman-client-proxy/rest/publications` with HTTP headers
```
X-Forwarded-Host=laymanproxy.com
X-Forwarded-Prefix=/layman-client-proxy
```
then response will change to

```json
[
  {
    "workspace": "my_workspace",
    "publication_type": "layer",
    "name": "my_layer",
    "url": "https://laymanproxy.com/layman-client-proxy/rest/publications",
    ...
  },
  ...
]
```

Currently, value of X-Forwarded headers affects following URLs:
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
* [GET Workspace Map File](rest.md#get-workspace-map-file)
  * some URLs of each [internal layer](models.md#internal-map-layer):
    * `url` key
    * `protocol`.`url` key
    * each `legends` key if its HTTP protocol and netloc corresponds with `url` or `protocol`.`url`
    * `style` key if its HTTP protocol and netloc corresponds with `url` or `protocol`.`url`
  * NOTE: If client proxy protocol, host, or URL path prefix was used in URLs in uploaded file, then such values are also replaced with values according to X-Forwarded header values. Default values are used for requests without X-Forwarded headers (protocol is the one from [LAYMAN_CLIENT_PUBLIC_URL](env-settings.md#layman_client_public_url), host is [LAYMAN_PROXY_SERVER_NAME](env-settings.md#layman_proxy_server_name), and path prefix is empty string).
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
* [PATCH Workspace Layer](rest.md#patch-workspace-layer)
  * `url` key
  * `wms`.`url` key
  * `wfs`.`url` key
  * `style`.`url` key
  * `thumbnail`.`url` key
  * `metadata`.`comparison_url` key
* [PATCH Workspace Map](rest.md#patch-workspace-map)
  * `url` key
  * `file`.`url` key
  * `thumbnail`.`url` key
  * `metadata`.`comparison_url` key
* [OGC endpoints](endpoints.md)
  * Headers `X-Forwarded-For`, `X-Forwarded-Path`, `Forwarded` and `Host` are ignored
  * [WMS endpoints](endpoints.md#web-map-service)
    * all requests URLs
    * all legend URLs
  * [WFS endpoints](endpoints.md#web-feature-service)
    * all operations URLs

Values of X-Forwarded headers does not affect response values of [GET Workspace Layer Metadata Comparison](rest.md#get-workspace-layer-metadata-comparison) and [GET Workspace Map Metadata Comparison](rest.md#get-workspace-map-metadata-comparison).
