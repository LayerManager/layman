# Recommendations for implementing Layman's client

Any Layman's client (web, user-agent, mobile, or desktop) that implements [OAuth2 authentication](index.md) should implement all responsibilities of [Layman Test Client](index.md#layman-test-client) (LTC). As there are many ways how to accomplish it, this page provides some recommendations.

## Appropriate Code Grant
OAuth2 specifies many ways how to authorize *client* and how *client* obtains access and refresh tokens. These ways are called [authorization grants](https://tools.ietf.org/html/rfc6749#section-1.3). For LTC, the **Authorization Code** grant was chosen. For [native clients (desktop and mobile)](https://tools.ietf.org/html/draft-ietf-oauth-security-topics-13#section-3.1.1), as well as for [user agent applications](https://tools.ietf.org/html/draft-ietf-oauth-browser-based-apps-04#section-7.1), [**Authorization Code with PKCE**](https://tools.ietf.org/html/rfc7636) (RFC7636) is recommended.

Both **Authorization Code** and **Authorization Code with PKCE** grant flows between *client* and *authorization server* are described in [Django OAuth Toolkit documentation](https://django-oauth-toolkit.readthedocs.io/en/latest/getting_started.html#authorization-code).

## Storing Tokens on a Client
An important decision when implementing OAuth2 *client* is where to store access tokens and refresh tokens. The recommendations differ based on [*client profile*](https://tools.ietf.org/html/rfc6749#section-2.1).
 
[*Web Applications*](https://tools.ietf.org/html/rfc6749#section-2.1) are able to store tokens either on server side or client side. There exists quite straightforward recommendations (see e.g. [auth0](https://auth0.com/docs/security/store-tokens#regular-web-apps), [DZone](https://dzone.com/articles/security-best-practices-for-managing-api-access-to) or [StackExchange](https://security.stackexchange.com/a/209388)). Generally three options are available:
1. Store access tokens in browser memory. It would mean to provide new authorization request against authorization server and manual end-user authorization consent on every page open or page reload.
2. Store access tokens in both secure and HTTP-only cookies. This option requires to have server side to set access tokens in cookies, and to refresh them using refresh tokens. Also refresh tokens need to be saved on server side.
3. Store access token on server side in any well-protected database.

Because option 1 is totally impractical and both options 2 and 3 require server side, it was decided to implement option 3 in LTC as the most secure one (it does not expose access token to client/browser at all).

[*User Agent Applications*](https://tools.ietf.org/html/rfc6749#section-2.1) are potentially the most dangerous ones. As described in *Web Applications* section, storing tokens in memory is impractical, and other options require server side, so user agent application actually becomes *Web Application*.

[*Native Applications*](https://tools.ietf.org/html/rfc6749#section-2.1) (i.e. desktop or mobile) should store tokens in any well-protected database.
