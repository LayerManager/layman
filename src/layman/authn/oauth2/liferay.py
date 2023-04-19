import requests
from layman import settings

AUTH_URLS = settings.OAUTH2_AUTH_URLS
INTROSPECTION_URL = settings.OAUTH2_INTROSPECTION_URL
INTROSPECTION_SUB_KEY = settings.OAUTH2_INTROSPECTION_SUB_KEY
USER_PROFILE_URL = settings.OAUTH2_USER_PROFILE_URL


def get_open_id_claims(access_token):
    result = {}
    resposne = requests.get(USER_PROFILE_URL, headers={
        'Authorization': f'Bearer {access_token}',
    })
    resposne.raise_for_status()
    r_json = resposne.json()
    result['sub'] = r_json['userId']
    result['email'] = r_json['emailAddress']
    result['email_verified'] = r_json['emailAddressVerified']
    name = [
        n for n in [
            r_json.get('firstName', None),
            r_json.get('middleName', None),
            r_json.get('lastName', None)
        ]
        if n is not None and len(n) > 0
    ]
    name = " ".join(name)
    result['name'] = name
    result['given_name'] = r_json.get('firstName')
    result['family_name'] = r_json.get('lastName')
    result['middle_name'] = r_json.get('middleName')
    result['preferred_username'] = r_json.get('screenName')
    result['updated_at'] = r_json.get('modifiedDate')
    return result
