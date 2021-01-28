import pytest

from . import upgrade_v1_10
from layman import app, settings
from layman.http import LaymanError
from layman.common import prime_db_schema


@pytest.mark.usefixtures('ensure_layman')
def test_check_usernames_for_wms_suffix():
    username = 'test_check_usernames_for_wms_suffix'
    username_wms = 'test_check_usernames_for_wms_suffix' + settings.LAYMAN_GS_WMS_WORKSPACE_POSTFIX

    with app.app_context():
        prime_db_schema.ensure_workspace(username)
        upgrade_v1_10.check_usernames_for_wms_suffix()

        prime_db_schema.ensure_workspace(username_wms)
        with pytest.raises(LaymanError) as exc_info:
            upgrade_v1_10.check_usernames_for_wms_suffix()
        assert exc_info.value.data['workspace'] == username_wms
