from . import util
from layman import settings


authorize = util.authorize


def is_user_in_access_rule(username, access_rule_names):
    return settings.RIGHTS_EVERYONE_ROLE in access_rule_names \
        or (username and username in access_rule_names)


get_publication_access_rights = util.get_publication_access_rights
