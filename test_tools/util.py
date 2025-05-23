import copy
import time
from zipfile import ZipFile
import os
import requests
from requests.exceptions import ConnectionError
from PIL import Image, ImageChops

from layman import app, celery, settings
from layman.util import url_for as layman_url_for


def url_for(endpoint, *, internal=True, **values):
    return layman_url_for(endpoint, internal=internal, **values)


def url_for_external(endpoint, **values):
    assert not values.get('internal', False)
    return url_for(endpoint, internal=False, **values)


# utils
def wait_for_url(url, max_attempts, sleeping_time):
    attempt = 1
    while True:
        # print(f"Waiting for URL {url}, attempt {attempt}")
        try:
            # Just checking the url, no need to store result
            requests.get(url, timeout=settings.DEFAULT_CONNECTION_TIMEOUT)
            break
        except ConnectionError as exception:
            if attempt == max_attempts:
                print(f"Max attempts reached")
                raise exception
            attempt += 1
        time.sleep(sleeping_time)


def compare_images(image1, image2):
    expected_image = Image.open(image1)
    current_image = Image.open(image2)

    diff_image = ImageChops.difference(expected_image, current_image)

    diffs = 0

    for x_value in range(diff_image.width):
        for y_value in range(diff_image.height):
            pixel_diff = diff_image.getpixel((x_value, y_value))
            # RGBA bands
            if isinstance(pixel_diff, tuple):
                if len(pixel_diff) == 4:
                    if pixel_diff != (0, 0, 0, 0) and \
                            (expected_image.getpixel((x_value, y_value))[3] > 0 or current_image.getpixel((x_value, y_value))[3] > 0):
                        diffs += 1
                elif len(pixel_diff) == 3:
                    if pixel_diff != (0, 0, 0):
                        diffs += 1
                else:
                    raise NotImplementedError(f"Unsupported number of bands: {len(pixel_diff)}")
            # one band, e.g. 8-bit PNG
            elif isinstance(pixel_diff, int):
                if pixel_diff != 0:
                    diffs += 1
            else:
                raise NotImplementedError(f"Unsupported type of value {type(pixel_diff)}")

    return diffs


def assert_error(expected, thrown):
    for key, exp_value in expected.items():
        thrown_value = getattr(thrown.value, key)
        assert thrown_value == exp_value, f'key={key}, thrown_value={thrown_value}, expected={exp_value}'


def assert_async_error(expected, thrown):
    expected = copy.deepcopy(expected)
    expected.pop('http_code', None)
    for key, value in expected.items():
        thrown_key = key if key != 'data' else 'detail'
        assert thrown[thrown_key] == value, f'key={key}, thrown_dict={thrown}, expected={expected}'


def compress_files(filepaths, *, compress_settings, output_dir):
    file_name = (compress_settings.archive_name
                 if compress_settings and compress_settings.archive_name is not None
                 else 'temporary_zip_file') + '.zip'
    inner_directory = compress_settings.inner_directory if compress_settings else None
    inner_filename = compress_settings.file_name if compress_settings else None
    zip_file = os.path.join(output_dir, file_name)
    with ZipFile(zip_file, 'w') as zipfile:
        for file in filepaths:
            filename = os.path.split(file)[1]
            _, ext = filename.split('.', 1)
            final_filename = (inner_filename + '.' + ext) if inner_filename else filename
            inner_path = os.path.join(inner_directory, final_filename) if inner_directory else final_filename
            zipfile.write(file, arcname=inner_path)
    return zip_file


def abort_publication_chain(workspace, publ_type, name):
    with app.app_context():
        celery.abort_publication_chain(workspace,
                                       publ_type,
                                       name,
                                       )
