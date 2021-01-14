import os
from distutils.dir_util import copy_tree


def ensure_data_dir(data_dir, data_dir_initial):
    if not os.listdir(data_dir):
        copy_tree(data_dir_initial, data_dir)
