import time
import requests
from requests.exceptions import ConnectionError
from PIL import Image, ImageChops

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
    expected.pop('http_code')
    for key, value in expected.items():
        assert thrown[key] == value, f'key={key}, thrown_dict={thrown}, expected={expected}'
