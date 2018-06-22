from flask import Flask, request, flash, redirect
from werkzeug.utils import secure_filename
from util import LAYMAN_DATA_PATH
import os

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

@app.route('/')
def index():
    return redirect('/static/index.html')

@app.route('/layers', methods=['POST'])
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect('/static/index.html')
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect('/static/index.html')
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(LAYMAN_DATA_PATH, filename))
        return "{filename} uploaded".format(filename=filename)