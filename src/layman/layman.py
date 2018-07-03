import os

from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename

from .http import error
from .settings import LAYMAN_DATA_PATH

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

@app.route('/')
def index():
    return redirect('/static/index.html')

@app.route('/layers', methods=['POST'])
def upload_file():
    app.logger.info('upload_file 2')
    if 'file' not in request.files:
        return error('Missing parameter "file"')
    files = request.files.getlist("file")
    if len(files) == 0:
        return error('Parameter "file" contains no file')
    for file in files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(LAYMAN_DATA_PATH, filename))
    return jsonify({'message': '{} files uploaded'.format(len(files))}), 200
