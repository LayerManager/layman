

def save_files(files, filepath_mapping):
    for file in files:
        if filepath_mapping[file.filename] is None:
            continue
        # logger.info(
        #     f'Saving file {file.filename} as {filepath_mapping[file.filename]}')
        file.save(filepath_mapping[file.filename])


