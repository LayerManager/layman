import pytest

from layman import LaymanError
from test_tools import process_client


# pylint: disable=too-few-public-methods
@pytest.mark.usefixtures('ensure_layman_module')
class TestPublication:
    workspace = 'dynamic_test_post_with_uuid'
    name = 'test_post_by_uuid'

    @pytest.mark.parametrize('publ_type', process_client.PUBLICATION_TYPES)
    def test_post(self, publ_type):
        uuid = '959c95fb-ab54-47a6-9694-402926b8fd29'
        response = process_client.publish_workspace_publication(publ_type, self.workspace, self.name, uuid=uuid)
        assert response['uuid'] == uuid

        with pytest.raises(LaymanError) as exc_info:
            process_client.publish_workspace_publication(publ_type, self.workspace, self.name, uuid=uuid)
        assert exc_info.value.http_code == 400
        assert exc_info.value.code == 2
        assert exc_info.value.data['message'] == f'UUID `959c95fb-ab54-47a6-9694-402926b8fd29` value already in use'
        assert exc_info.value.data['parameter'] == 'uuid'

        process_client.delete_workspace_publication(publ_type, self.workspace, self.name)

    @pytest.mark.parametrize('publ_type', process_client.PUBLICATION_TYPES)
    def test_post_invalid_uuid(self, publ_type, ):
        uuid = '959c95fb-402926b8fd29'
        with pytest.raises(LaymanError) as exc_info:
            process_client.publish_workspace_publication(publ_type, self.workspace, self.name, uuid=uuid)
        assert exc_info.value.http_code == 400
        assert exc_info.value.code == 2
        assert exc_info.value.data['message'] == f'UUID `959c95fb-402926b8fd29` is not valid uuid'
        assert exc_info.value.data['parameter'] == 'uuid'
