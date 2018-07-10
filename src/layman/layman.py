import os
import re
import pathlib

from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename

from .http import error
from .settings import LAYMAN_DATA_PATH, MAIN_FILE_EXTENSIONS
from .util import to_safe_layer_name, get_main_file_name, get_file_name_mappings

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

@app.route('/')
def index():
    return redirect('/static/index.html')

@app.route('/layers', methods=['POST'])
def upload_file():
    app.logger.info('upload_file')

    # user
    if 'user' not in request.form:
        return error(1, {'parameter': 'user'})

    username = request.form['user']
    username_re = r"^[a-z][a-z0-9_]*$"
    if not re.match(username_re, username):
        return error(2, {'parameter': 'user', 'expected': username_re})

    userdir = os.path.join(LAYMAN_DATA_PATH, username)
    pathlib.Path(userdir).mkdir(exist_ok=True)

    # file 1/2
    if 'file' not in request.files:
        return error(1, {'parameter': 'file'})
    files = request.files.getlist("file")
    filenames = list(map(lambda f: f.filename, files))

    main_filename = get_main_file_name(filenames)
    if main_filename is None:
        return error(2, {'parameter': 'file', 'expected': \
            'At least one file with any of extensions: '+\
            ', '.join(MAIN_FILE_EXTENSIONS)})


    # name
    if 'name' in request.form:
        layername = request.form['name']
    else:
        layername = os.path.splitext(main_filename)[0]
    layername = to_safe_layer_name(layername)



    # file 2/2
    filename_mapping, filepath_mapping = get_file_name_mappings(
        filenames, main_filename, layername, userdir
    )
    conflict_paths = [filename_mapping[k]
                      for k, v in filepath_mapping.items()
                      if v is not None and os.path.isfile(v)]
    if len(conflict_paths) > 0:
        return error(3, conflict_paths)
    for file in files:
        if filepath_mapping[file.filename] is None:
            continue
        app.logger.info('Saving file {} as {}'.format(
            file.filename, filepath_mapping[file.filename]))
        file.save(filepath_mapping[file.filename])
    n_uploaded_files = len({k:v
                            for k, v in filepath_mapping.items()
                            if v is not None})
    return jsonify({
        'message': '{} files uploaded, {} ignored.'.format(
            n_uploaded_files, len(files)-n_uploaded_files),
        'saved_files': filename_mapping
    }), 200
