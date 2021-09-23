import os
import pathlib


def save_files(files, filepath_mapping, *, prefix=None):
    for file in files:
        if filepath_mapping[file.filename] is None:
            continue
        # logger.info(
        #     f'Saving file {file.filename} as {filepath_mapping[file.filename]}')
        filepath = filepath_mapping[file.filename]
        full_file_path = os.path.join(prefix, filepath) if prefix else filepath
        directory = os.path.dirname(full_file_path)
        pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
        file.save(full_file_path)
