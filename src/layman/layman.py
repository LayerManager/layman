import os
import re

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
    app.logger.info('upload_file')
    if 'user' not in request.form:
        return error(1, {'parameter': 'user'})

    username = request.form['user']
    username_re = r"^[a-zA-Z]\w*$"
    if not re.match(username_re, username):
        return error(2, {'parameter': 'user', 'expected': username_re})



    if 'file' not in request.files:
        return error(1, {'parameter': 'file'})
    files = request.files.getlist("file")
    for file in files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(LAYMAN_DATA_PATH, filename))
    return jsonify({'message': '{} files uploaded'.format(len(files))}), 200
