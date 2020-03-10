from multiprocessing import Process
import pytest
import time
import os
import filecmp
import difflib

import sys
del sys.modules['layman']

from layman import app as app
from layman import settings

from layman.common.micka import util as common_util
from .util import parse_md_properties


def test_fill_template():
    xml_path = 'src/layman/layer/micka/util_test_filled_template.xml'
    with open(xml_path, 'r') as xml_file:
        props = parse_md_properties(xml_file, ['md_file_identifier'])
    print(f"props={props}")
