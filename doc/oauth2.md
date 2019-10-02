# Authentication with OAuth2

Layman is able to authenticate against [OAuth 2.0](https://oauth.net/2/) provider. [Liferay Portal](https://portal.liferay.dev/docs/7-1/deploy/-/knowledge_base/d/oauth-2-0) is currently the only supported OAuth2 provider, however supporting [other OAuth2 providers](https://en.wikipedia.org/wiki/List_of_OAuth_providers) (e.g. Google or Facebook) should be quite straightforward in future.


## Roles

### OAuth2 Terminology
From [RFC6749](https://tools.ietf.org/html/rfc6749#section-1.1):
- *resource owner*:
      An entity capable of granting access to a protected resource.
      When the resource owner is a person, it is referred to as an
      end-user.

- *resource server*:
      The server hosting the protected resources, capable of accepting
      and responding to protected resource requests using access tokens.

- *client*:
      An application making protected resource requests on behalf of the
      resource owner and with its authorization.  The term "client" does
      not imply any particular implementation characteristics (e.g.,
      whether the application executes on a server, a desktop, or other
      devices).

- *authorization server*:
      The server issuing access tokens to the client after successfully
      authenticating the resource owner and obtaining authorization.


### Layman
Layman acts as *resource server*. On every request to REST API, Layman accepts OAuth2 [access token](https://tools.ietf.org/html/rfc6749#section-1.4) from a *client* and validates access token against *authorization server* to authenticate *resource owner* (i.e. end-user). The access token is validated token against *authorization server* by OAuth2 mechanism called [Token Introspection](https://oauth.net/2/token-introspection/) (RFC 7662). Furthermore, Layman is responsible for fetching user-related metadata from *authorization server* using provider-specific endpoint.

### Liferay Portal
[Liferay Portal](https://portal.liferay.dev/docs/7-1/deploy/-/knowledge_base/d/oauth-2-0) acts as *authorization server*.

### Layman Test Client
[Layman Test Client](https://github.com/jirik/layman-test-client) (LTC) acts as *client*. It is responsible for
- asking appropriate [authorization grant](https://tools.ietf.org/html/rfc6749#section-1.3) from *resource server* to get valid access token
- safely storing access token and [refresh token](https://oauth.net/2/grant-types/refresh-token/) during end-user's session
- fetching user-related metadata from Layman's [GET Current User](https://github.com/jirik/layman/blob/auth-stage2/doc/rest.md#get-current-user)
- reserving username for the end-user on Layman's side using [PATCH Current User](https://github.com/jirik/layman/blob/auth-stage2/doc/rest.md#patch-current-user) if end-user does not have any username yet
- passing access token to Layman REST API with every request
- refreshing access token using refresh token

Key feature of LTC is that is has client side as well as server side that is completely separate from Layman REST API. The server side exists to [keep access tokens and refresh tokens in secret](oauth2-client-recommendations.md#storing-tokens-on-a-client). 

Although LTC is currently the only OAuth2 client for Layman, there is an intention to implement also other clients, e.g. for QGIS or HS Layers. If you want to implement such client, see [recommendations for implementing Layman's client](oauth2-client-recommendations.md).


## Communication
### Initial Authorization using Authorization Code
**Authorization Code** flow between *client* and *authorization server* is described in [Liferay documentation](https://portal.liferay.dev/docs/7-1/deploy/-/knowledge_base/d/authorizing-account-access-with-oauth2#authorization-code-flow).

Schema specific for LTC, distinguishing client side and server side of LTC:

![oauth2-auth-code.puml](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/jirik/layman/auth-stage2/doc/oauth2-auth-code.puml) 

### Request Layman REST API
After successful authorization, *client* is able to communicate with Layman REST API. To authenticate using OAuth2, every request to Layman REST API must contain two HTTP headers:
- `Authorization`
- `AuthorizationIssUrl`

**Authorization** header contains access token according to [RFC6750 Bearer Token Usage](https://tools.ietf.org/html/rfc6750#section-2.1). Structure of its value is `"Bearer <access token>"`.

**AuthorizationIssUrl** header is Layman-specific header and it contains URL of [Authorization Endpoint](https://tools.ietf.org/html/rfc6749#section-3.1), e.g. `"http://localhost:8082/o/oauth2/authorize"`. LTC uses the value from LIFERAY_OAUTH2_AUTH_URL setting.

Because access token is known only on server side of LTC and not to client side, every request from client side to Layman REST API goes through **proxy** on LTC server side. The proxy adds `Authorization` and `AuthorizationIssUrl` headers to the request and forward it to the Layman. To authenticate end-user, Layman then validates access token on *authorization server* using [Token Introspection](https://oauth.net/2/token-introspection/) mechanism.
 
General schema of any request to Layman REST API:

![oauth2-rest.puml](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/jirik/layman/auth-stage2/doc/oauth2-rest.puml)


### Fetch User-Related Metadata
Fetching user-related metadata happens automatically immediately after successful initial authorization by [GET Current User](https://github.com/jirik/layman/blob/auth-stage2/doc/rest.md#get-current-user).

![oauth2-get-current-user.puml](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/jirik/layman/auth-stage2/doc/oauth2-get-current-user.puml)

The fetch should happen regularly during end-user session to test if authentication (access token) is still valid. 
 

### Reserve Username
Immediately after the first [fetch of user-related metadata](#fetch-user-related-metadata), *client* should check if **username** was already registered for authenticated end-user (response to [GET Current User](https://github.com/jirik/layman/blob/auth-stage2/doc/rest.md#get-current-user) contains `username`) or not (response does not contains `username`). If username was not registered yet, it is recommended to register it as soon as possible, because it's required when user wants to publish any data.

Username is registered by [PATCH Current User](https://github.com/jirik/layman/blob/auth-stage2/doc/rest.md#patch-current-user). Username can be either generated automatically (this approach is used by LTC) or set manually; this is controlled by `adjust_username` parameter.

![oauth2-patch-current-user.puml](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/jirik/layman/auth-stage2/doc/oauth2-patch-current-user.puml) 

### Refresh Access Token
During end-user's session, *client* keeps both access tokens and refresh token. When access token expires (or it's lifetime is close), *client* should use refresh token to generate new access token at [Token Endpoint](https://tools.ietf.org/html/rfc6749#section-3.2).

Refreshing flow between *client* and *authorization server* is described in [Liferay issue](https://issues.liferay.com/browse/OAUTH2-167). In case of LTC, refreshing happens automatically on any request to Layman REST API if access token expired.

Schema specific for LTC:
![oauth2-refresh.puml](http://www.plantuml.com/plantuml/proxy?src=https://raw.githubusercontent.com/jirik/layman/auth-stage2/doc/oauth2-refresh.puml) 


## Settings

To enable OAuth2 authentication in Layman, adjust following settings in `layman_settings.py`:
- AUTHN_MODULES
- AUTHN_OAUTH2_PROVIDERS
- LIFERAY_OAUTH2_AUTH_URLS
- LIFERAY_OAUTH2_INTROSPECTION_URL
- LIFERAY_OAUTH2_USER_PROFILE_URL
- LIFERAY_OAUTH2_CLIENTS

Sample values for OAuth2 authentication can be found in [`layman_settings_dev.py`](../src/layman_settings_dev.py).

### Liferay Settings
Every *client* must be registered in Liferay as *application*, as described in [Liferay documentation](https://portal.liferay.dev/docs/7-1/deploy/-/knowledge_base/d/oauth-2-0#creating-an-application). For LTC, fill in following settings:
- **Website URL** should point to application's home page, e.g. `http://localhost:3000/`.
- **Callback URIs** must contain URL of OAuth2 [*Redirection Endpoint*](https://tools.ietf.org/html/rfc6749#section-3.1.2). In case of LTC, the value is the same as LTC setting LIFERAY_OAUTH2_CALLBACK_URL.
- **Client Profile**: Web Application
- **Allowed Authorization Types**:
    - Authorization Code
    - Refresh Token
- **Supported Features**:
    - Token Introspection

Furthermore, check "read your personal user data" (liferay-json-web-services.everything.read.userprofile) in **Scopes** tab. This scope will enable `/api/jsonws/user/get-current-user` endpoint to provide user-related metadata to Layman.

After registration, add **Client ID** and **Client Secret** pair to Layman's setting LIFERAY_OAUTH2_CLIENTS.

### Layman Test Client Settings
Check following environment variables of LTC:
- LIFERAY_OAUTH2_CLIENT_ID: **Client ID** from Liferay
- LIFERAY_OAUTH2_SECRET: **Client Secret** from Liferay
- LIFERAY_OAUTH2_AUTH_URL: URL of [Authorization Endpoint](https://tools.ietf.org/html/rfc6749#section-3.1), usually the same as the first URL from Layman's LIFERAY_OAUTH2_AUTH_URLS
- LIFERAY_OAUTH2_TOKEN_URL: URL of [Token Endpoint](https://tools.ietf.org/html/rfc6749#section-3.2). In case of liferay, it's something like `<http or https>://<Liferay domain and port>/o/oauth2/token`
- LIFERAY_OAUTH2_CALLBACK_URL: URL of [Redirection Endpoint](https://tools.ietf.org/html/rfc6749#section-3.1.2), the value is `<http or https>://<LTC domain, port, and path prefix>/auth/oauth2-liferay/callback`.
- LAYMAN_USER_PROFILE_URL: URL of Layman's [GET Current User](https://github.com/jirik/layman/blob/auth-stage2/doc/rest.md#get-current-user)



