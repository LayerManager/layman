import os

from flask import url_for

from .__init__ import get_user_dir


def get_layer_info(username, layername):
    thumbnail_path = get_layer_thumbnail_path(username, layername)
    if thumbnail_path is not None:
        return {
            'thumbnail': {
                'url': url_for('get_layer_thumbnail', username=username,
                               layername=layername)
            }
        }
    return {}


def get_layer_thumbnail_path(username, layername):
    userdir = get_user_dir(username)
    thumbnail_path = os.path.join(userdir, layername+'.thumbnail.png')
    if os.path.exists(thumbnail_path):
        thumbnail_path = os.path.relpath(thumbnail_path, userdir)
        return thumbnail_path
    return None