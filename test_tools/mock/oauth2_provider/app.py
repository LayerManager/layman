from flask import Flask, request, jsonify, Blueprint, current_app


TOKEN_HEADER = 'Authorization'


def create_app(app_config):
    app = Flask(__name__)
    app_config.setdefault('OAUTH2_USERS', {})
    for key, value in app_config.items():
        if key == 'OAUTH2_USERS':
            tok2is = {}
            tok2is.update(token_2_introspection)
            tok2prof = {}
            tok2prof.update(token_2_profile)
            u_idx = 30000
            for username, userdef in value.items():
                sub = userdef.get('sub') if userdef and userdef.get('sub') else f'{u_idx}'
                assert sub not in [
                    introsp['sub'] for introsp in tok2is.values()
                ]
                tok2is[username] = {
                    'sub': sub
                }
                tok2prof[username] = {
                    "emailAddress": f"{username}@oauth2.org",
                    "firstName": f"{username}",
                    "lastName": f"{username}",
                    "middleName": "",
                    "screenName": f"{username}",
                    "userId": sub,
                }
                if userdef:
                    tok2prof[username].update(userdef)
                u_idx += 1
            app.config['OAUTH2_TOKEN_2_INTROSPECTION'] = tok2is
            app.config['OAUTH2_TOKEN_2_PROFILE'] = tok2prof
        else:
            app.config[key] = value
    app.register_blueprint(introspection_bp, url_prefix='/rest/test-oauth2/')
    app.register_blueprint(user_profile_bp, url_prefix='/rest/test-oauth2/')
    return app


introspection_bp = Blueprint('rest_test_oauth2_introspection', __name__)
user_profile_bp = Blueprint('rest_test_oauth2_user_profile', __name__)

token_2_introspection = {
    'abc': {
        'sub': "20139",
    },
    'test2': {
        'sub': "20140",
    },
    'test3': {
        'sub': "20141",
    },
    'test_patch_current_user_user1': {
        'sub': "20142",
    },
    'test_patch_current_user_user2': {
        'sub': "20143",
    },
}
token_2_profile = {
    'abc': {
        "emailAddress": "test@oauth2.org",
        "firstName": "Test",
        "lastName": "Test",
        "middleName": "",
        "screenName": "test",
        "userId": "20139",
    },
    'test2': {
        "emailAddress": "test2@oauth2.org",
        "firstName": "Test",
        "lastName": "Test",
        "middleName": "",
        "screenName": "test2",
        "userId": "20140",
    },
    'test3': {
        "emailAddress": "test3@oauth2.org",
        "firstName": "Test",
        "lastName": "Test",
        "middleName": "",
        "screenName": "test3",
        "userId": "20141",
    },
    'test_patch_current_user_user1': {
        "emailAddress": "test_patch_current_user_user1_email@oauth2.org",
        "firstName": "FirstName",
        "lastName": "LastName",
        "middleName": "MiddleName",
        "screenName": "test_patch_current_user_user1 screen name",
        "userId": "20142",
    },
    'test_patch_current_user_user2': {
        "emailAddress": "test_patch_current_user_user2@oauth2.org",
        "firstName": "Test",
        "lastName": "Test",
        "middleName": "",
        "screenName": "test_patch_current_user_user2",
        "userId": "20143",
    },
}


@introspection_bp.route('introspection', methods=['POST'])
def post():
    is_active = request.args.get('is_active', None)
    is_active = is_active is not None and is_active.lower() == 'true'

    access_token = request.form.get('token')
    assert access_token in current_app.config['OAUTH2_TOKEN_2_INTROSPECTION'], f"access_token={access_token}, current_app.config['OAUTH2_TOKEN_2_INTROSPECTION']={current_app.config['OAUTH2_TOKEN_2_INTROSPECTION']}"
    result = {
        "active": is_active, "client_id": "VECGuQb00tWt8HZNkA4cxu6dnoQD5pF6Up3daAoK", "exp": 1568981517,
        "iat": 1568980917,
        "sub": "20139", "token_type": "Bearer",
        "username": "Test Test", "company.id": "20099"
    }
    result.update(current_app.config['OAUTH2_TOKEN_2_INTROSPECTION'][access_token])

    return jsonify(result), 200


@user_profile_bp.route('user-profile', methods=['GET'])
def get():
    access_token = request.headers.get(TOKEN_HEADER).split(' ')[1]
    assert access_token in current_app.config['OAUTH2_TOKEN_2_PROFILE']

    result = {
        "agreedToTermsOfUse": False,
        "comments": "",
        "companyId": "20099",
        "contactId": "20141",
        "createDate": 1557361648854,
        "defaultUser": False,
        "emailAddress": "test@oauth2.org",
        "emailAddressVerified": True,
        "externalReferenceCode": "",
        "facebookId": "0",
        "failedLoginAttempts": 0,
        "firstName": "Test",
        "googleUserId": "",
        "graceLoginCount": 0,
        "greeting": "Welcome Test Test!",
        "jobTitle": "",
        "languageId": "en_US",
        "lastFailedLoginDate": None,
        "lastLoginDate": 1565768756360,
        "lastLoginIP": "172.19.0.1",
        "lastName": "Test",
        "ldapServerId": "-1",
        "lockout": False,
        "lockoutDate": None,
        "loginDate": 1568805421539,
        "loginIP": "172.18.0.1",
        "middleName": "",
        "modifiedDate": 1568805421548,
        "mvccVersion": "11",
        "openId": "",
        "portraitId": "0",
        "reminderQueryAnswer": "aa",
        "reminderQueryQuestion": "what-is-your-father's-middle-name",
        "screenName": "test",
        "status": 0,
        "timeZoneId": "UTC",
        "userId": "20139",
        "uuid": "4ef84411-749a-e617-6191-10e0c6a7147b",
        "FLASK_DEBUG": "1" if current_app.debug else '',
    }
    result.update(current_app.config['OAUTH2_TOKEN_2_PROFILE'][access_token])

    return jsonify(result), 200
