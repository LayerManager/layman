import pytest

from tests.dynamic_data.publications import common_publications as publications
from . import util, process_client


@pytest.mark.parametrize('param_parametrization, only_first_parametrization, default_params, exp_result', [
    (
        {
            'compress': {False: '', True: 'zipped'},
        },
        True,
        None,
        [
            ('post', process_client.publish_workspace_publication, [], {
                'compress': False,
            }),
        ],
    ),
    (
        {
            'compress': {False: '', True: 'zipped'},
        },
        False,
        None,
        [
            ('post', process_client.publish_workspace_publication, [], {
                'compress': False,
            }),
            ('post_zipped', process_client.publish_workspace_publication, [], {
                'compress': True,
            }),
            ('patch', process_client.patch_workspace_publication, [publications.DEFAULT_POST], {
                'compress': False,
            }),
            ('patch_zipped', process_client.patch_workspace_publication, [publications.DEFAULT_POST], {
                'compress': True,
            }),
        ],
    ),
    (
        {
            'with_chunks': {False: 'sync', True: 'chunks'},
            'compress': {False: '', True: 'zipped'},
        },
        True,
        None,
        [
            ('post_sync', process_client.publish_workspace_publication, [], {
                'with_chunks': False,
                'compress': False,
            }),
        ],
    ),
    (
        {
            'with_chunks': {False: 'sync', True: 'chunks'},
            'compress': {False: '', True: 'zipped'},
        },
        False,
        None,
        [
            ('post_sync', process_client.publish_workspace_publication, [], {
                'with_chunks': False,
                'compress': False,
            }),
            ('post_sync_zipped', process_client.publish_workspace_publication, [], {
                'with_chunks': False,
                'compress': True,
            }),
            ('post_chunks', process_client.publish_workspace_publication, [], {
                'with_chunks': True,
                'compress': False,
            }),
            ('post_chunks_zipped', process_client.publish_workspace_publication, [], {
                'with_chunks': True,
                'compress': True,
            }),
            ('patch_sync', process_client.patch_workspace_publication, [publications.DEFAULT_POST], {
                'with_chunks': False,
                'compress': False,
            }),
            ('patch_sync_zipped', process_client.patch_workspace_publication, [publications.DEFAULT_POST], {
                'with_chunks': False,
                'compress': True,
            }),
            ('patch_chunks', process_client.patch_workspace_publication, [publications.DEFAULT_POST], {
                'with_chunks': True,
                'compress': False,
            }),
            ('patch_chunks_zipped', process_client.patch_workspace_publication, [publications.DEFAULT_POST], {
                'with_chunks': True,
                'compress': True,
            }),
        ],
    ),
    (
        {
            'compress': {False: '', True: 'zipped'},
        },
        True,
        {'compress': True},
        [
            ('post_zipped', process_client.publish_workspace_publication, [], {
                'compress': True,
            }),
        ],
    ),
    (
        {
            'with_chunks': {False: 'sync', True: 'chunks'},
            'compress': {False: '', True: 'zipped'},
        },
        False,
        {'with_chunks': True},
        [
            ('post_chunks', process_client.publish_workspace_publication, [], {
                'with_chunks': True,
                'compress': False,
            }),
            ('post_chunks_zipped', process_client.publish_workspace_publication, [], {
                'with_chunks': True,
                'compress': True,
            }),
            ('patch_chunks', process_client.patch_workspace_publication, [publications.DEFAULT_POST], {
                'with_chunks': True,
                'compress': False,
            }),
            ('patch_chunks_zipped', process_client.patch_workspace_publication, [publications.DEFAULT_POST], {
                'with_chunks': True,
                'compress': True,
            }),
        ],
    ),
])
def test_get_test_case_parametrization(param_parametrization, only_first_parametrization, default_params, exp_result):
    result = util.get_test_case_parametrization(param_parametrization=param_parametrization,
                                                only_first_parametrization=only_first_parametrization,
                                                default_params=default_params,
                                                action_parametrization=publications.DEFAULT_ACTIONS,
                                                )
    assert result == exp_result
