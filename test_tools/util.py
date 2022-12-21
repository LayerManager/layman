import copy
import itertools
import time
from zipfile import ZipFile
import os
import requests
from requests.exceptions import ConnectionError
from PIL import Image, ImageChops

from layman import app, celery
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
            requests.get(url)
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
    thrown_dict = thrown.value.to_dict()
    for key, value in expected.items():
        if key == 'http_code':
            assert thrown.value.http_code == value, f'thrown_dict={thrown_dict}, expected={expected}'
        else:
            assert thrown_dict[key] == value, f'key={key}, thrown_dict={thrown_dict}, expected={expected}'


def assert_async_error(expected, thrown):
    expected = expected.copy()
    expected.pop('http_code', None)
    for key, value in expected.items():
        assert thrown[key] == value, f'key={key}, thrown_dict={thrown}, expected={expected}'


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


def sleep(seconds):
    time.sleep(seconds)


def abort_publication_chain(workspace, publ_type, name):
    with app.app_context():
        celery.abort_publication_chain(workspace,
                                       publ_type,
                                       name,
                                       )


def dictionary_product(source):
    names = list(source.keys())
    all_values = [list(source[p_name].keys()) for p_name in names]
    values = itertools.product(*all_values)
    param_dict = [{names[idx]: value for idx, value in enumerate(vals)} for vals in values]
    return param_dict


def get_test_case_parametrization(*, param_parametrization, only_first_parametrization, default_params, action_parametrization):
    result = list()

    parametrization = copy.deepcopy(param_parametrization)
    if default_params:
        for param_name, param_value in default_params.items():
            if param_name in parametrization:
                parametrization[param_name] = {default_params[param_name]: parametrization[param_name][param_value]}

    if only_first_parametrization:
        action_code, action_method, action_predecessor = action_parametrization[0]
        action_params = {param_name: next(iter(param_values.keys())) for param_name, param_values in parametrization.items()}
        postfix = '_'.join([action_code] + [parametrization[key][value]
                                            for key, value in action_params.items()
                                            if parametrization[key][value]])

        result = [(postfix, action_method, action_predecessor, action_params), ]
    else:
        for action_code, action_method, action_predecessor in action_parametrization:
            rest_param_dicts = dictionary_product(parametrization)
            for rest_param_dict in rest_param_dicts:
                postfix = '_'.join([action_code] + [parametrization[key][value]
                                                    for key, value in rest_param_dict.items()
                                                    if parametrization[key][value]])
                result.append((postfix, action_method, action_predecessor, rest_param_dict))

    return result
