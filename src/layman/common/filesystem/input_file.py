import os


def save_files(files, filepath_mapping, *, prefix=None):
    for file in files:
        if filepath_mapping[file.filename] is None:
            continue
        # logger.info(
        #     f'Saving file {file.filename} as {filepath_mapping[file.filename]}')
        file_path = os.path.join(prefix, filepath_mapping[file.filename]) if prefix else filepath_mapping[file.filename]
        file.save(file_path)
