from layman import patch_mode

PATCH_MODE = patch_mode.DELETE_IF_DEPENDANT


def get_publication_uuid(username, publication_type, publication_name):
    return None


def get_layer_info(username, layername):
    return dict()


def delete_layer(username, layer_name):
    pass


def patch_layer(username,
                layername,
                actor_name,
                style_type=None,
                title=None,
                access_rights=None,
                ):
    pass


def pre_publication_action_check(username,
                                 layername,
                                 actor_name,
                                 access_rights=None,
                                 ):
    pass


def post_layer(username,
               layername,
               access_rights,
               title,
               uuid,
               actor_name,
               style_type=None,
               ):
    pass


def get_metadata_comparison(username, publication_name):
    pass
