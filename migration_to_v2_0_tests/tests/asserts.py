
def assert_description(*, publ_detail, publication):
    assert publ_detail['description'] == publication.rest_args['description']
