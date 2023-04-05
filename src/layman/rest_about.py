import os
from flask import Blueprint, jsonify

from layman import upgrade

bp = Blueprint('rest_about', __name__)


def get_version_from_txt():
    file_path = '/code/version.txt'
    version, release_date = None, None
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            version = file.readline().strip()
            release_date = file.readline().strip()
    return version, release_date


def clean_version(version):
    if version[0] == 'v':
        version = version[1:]
    return version


@bp.route('/version', methods=['GET'])
def get_version():
    version, release_date = get_version_from_txt()

    migrations = dict()
    for migration_type in {upgrade.consts.MIGRATION_TYPE_DATA, upgrade.consts.MIGRATION_TYPE_SCHEMA, }:
        current_version = upgrade.get_current_version(migration_type)
        migrations[f'last-{migration_type}-migration'] =\
            f'{current_version[0]}.{current_version[1]}.{current_version[2]}-{current_version[3]}'
    migrations['last-migration'] = migrations[f'last-{upgrade.consts.MIGRATION_TYPE_SCHEMA}-migration']  # for backward compatibility
    result = {'about': {'applications': {'layman': {'version': clean_version(version),
                                                    'release-timestamp': release_date,
                                                    },
                                         'layman-test-client': {'version': clean_version(os.environ['LAYMAN_CLIENT_VERSION']),
                                                                },

                                         },
                        'data': {'layman': migrations,
                                 },
                        },
              }
    return jsonify(result), 200
