import os
import time
from zipfile import ZipFile

import requests
from requests.exceptions import ConnectionError


def wait_for_url(url, max_attempts, sleeping_time):
    attempt = 1
    while True:
        # print(f"Waiting for URL {url}, attempt {attempt}")
        try:
            # Just checking the url, no need to store result
            requests.get(url, timeout=1)
            break
        except ConnectionError as exception:
            if attempt == max_attempts:
                print(f"Max attempts reached")
                raise exception
            attempt += 1
        time.sleep(sleeping_time)


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
