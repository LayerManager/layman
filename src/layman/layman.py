import os
import re
import pathlib

from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename

from .http import error
from .settings import LAYMAN_DATA_PATH
from .util import to_safe_layer_name

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
    filenames = map(lambda f: f.filename, files)

    supported_exts = ['.shp']
    main_filename = next((fn for fn in filenames if os.path.splitext(fn)[1]
                          in supported_exts), None)
    if main_filename is None:
        return error(2, {'parameter': 'file', 'expected': \
            'At least one file with any of extensions: '+\
            ', '.join(supported_exts)})

    main_filename = os.path.splitext(main_filename)[0]
    files = list(filter(lambda f: f.filename.startswith(main_filename+'.'),
                      files))

    # name
    if 'name' in request.form:
        layername = request.form['name']
    else:
        layername = main_filename
    layername = to_safe_layer_name(layername)


    # file 2/2
    filename_mapping = {}
    filepath_mapping = {}
    for file in files:
        new_fn = layername+file.filename[len(main_filename):]
        filepath_mapping[file.filename] = os.path.join(userdir, new_fn)
        filename_mapping[file.filename] = new_fn
        if os.path.isfile(filepath_mapping[file.filename]):
            return error(3, 'File {} (sent as {}) already exists.'.format(
                new_fn, file.filename))
    for file in files:
        app.logger.info('Saving file {} as {}'.format(
            file.filename, filepath_mapping[file.filename]))
        file.save(filepath_mapping[file.filename])
    return jsonify({
        'message': '{} files uploaded'.format(len(list(files))),
        'saved_files': filename_mapping
    }), 200
