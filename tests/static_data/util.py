from layman import settings
from .. import static_data as data

KEY_AUTH = 'can'
KEY_NOT_AUTH = 'cannot'
KEY_USERS = 'users'
KEY_HEADERS = 'headers'
KEY_EXP_LIST = 'exp_list'


def get_users_and_headers_for_publication(workspace, publ_type, publication):
    users = data.USERS | {settings.ANONYM_USER, settings.NONAME_USER}
    is_personal_workspace = workspace in data.USERS

    result = {}
    for right in ['read', 'write']:
        result[right] = {}
        for type in [KEY_AUTH, KEY_NOT_AUTH]:
            result[right][type] = {}

        test_data = data.PUBLICATIONS[(workspace, publ_type, publication)][data.TEST_DATA].get('users_can_' + right)
        if test_data:
            result[right][KEY_AUTH][KEY_USERS] = test_data
            result[right][KEY_AUTH][KEY_EXP_LIST] = test_data
            result[right][KEY_AUTH][KEY_HEADERS] = [header for user, header in data.HEADERS.items() if user in test_data]
            result[right][KEY_NOT_AUTH][KEY_USERS] = {item for item in users if item not in test_data}
            result[right][KEY_NOT_AUTH][KEY_HEADERS] = [header for user, header in data.HEADERS.items() if user not in test_data] + [None]
        else:
            result[right][KEY_AUTH][KEY_USERS] = users
            result[right][KEY_AUTH][KEY_EXP_LIST] = {settings.RIGHTS_EVERYONE_ROLE}
            if is_personal_workspace:
                result[right][KEY_AUTH][KEY_EXP_LIST].add(workspace)
            result[right][KEY_AUTH][KEY_HEADERS] = list(data.HEADERS.values()) + [None]
            result[right][KEY_NOT_AUTH][KEY_USERS] = {}
            result[right][KEY_NOT_AUTH][KEY_HEADERS] = []
    return result
