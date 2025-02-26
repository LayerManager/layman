import copy
from layman import app, util as layman_util


def same_values_in_internal_and_rest(workspace, publ_type, name, rest_publication_detail):
    with app.app_context():
        publ_info = layman_util.get_publication_info(workspace, publ_type, name)
    publ_info = copy.deepcopy(publ_info)

    # adjust publ_info, see layman.common.util::clear_publication_info
    publ_info = {key: value for key, value in publ_info.items() if not (key.startswith('_') or key in ['id', 'type', ])}
    publ_info['updated_at'] = publ_info['updated_at'].isoformat()

    # adjust rest_publication_detail, see get_complete_(layer|map)_info
    rest_publication_detail = copy.deepcopy(rest_publication_detail)
    for key in ('layman_metadata', 'url'):
        rest_publication_detail.pop(key, None)

    if 'image_mosaic' not in rest_publication_detail:
        publ_info.pop('image_mosaic')

    assert publ_info == rest_publication_detail
