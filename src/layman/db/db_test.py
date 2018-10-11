import time
import shutil

from .__init__ import import_layer_vector_file_async
from layman.settings import *
from layman.filesystem import get_user_dir


def test_abort_import_layer_vector_file():
    username = 'testuser1'
    layername = 'ne_10m_admin_0_countries'
    src_dir = 'tmp/naturalearth/10m/cultural'
    userdir = get_user_dir(username)
    filename = layername+'.geojson'
    main_filepath = os.path.join(userdir, filename)

    crs_id = None
    shutil.copy(
        os.path.join(src_dir, filename),
        userdir
    )

    def abort_layer_import():
        p = import_layer_vector_file_async(username, layername, main_filepath,
                                        crs_id)
        time1 = time.time()
        while p.poll() is None:
            if(time.time()-time1 > 0.1):
                # print('terminating process')
                p.terminate()
            time.sleep(0.1)
            pass

        return_code = p.poll()
        return return_code

    return_code = abort_layer_import()
    assert return_code != 0

