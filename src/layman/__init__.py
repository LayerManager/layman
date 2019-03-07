from flask import Flask, redirect, jsonify

from .http import LaymanError
from .make_celery import make_celery
from .settings import *

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

celery_app = make_celery(app)

celery_tasks = {}


from layman.layer.rest_layers import bp as layers_bp
from layman.layer.rest_layer import bp as layer_bp
from layman.layer.rest_layer_chunk import bp as layer_chunk_bp
from layman.layer.rest_layer_thumbnail import bp as layer_thumbnail_bp


app.register_blueprint(layers_bp, url_prefix='/rest/<username>')
app.register_blueprint(layer_bp, url_prefix='/rest/<username>')
app.register_blueprint(layer_chunk_bp, url_prefix='/rest/<username>')
app.register_blueprint(layer_thumbnail_bp, url_prefix='/rest/<username>')


@app.route('/')
def index():
    return redirect('/static/test-client/index.html')


@app.errorhandler(LaymanError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.http_code
    return response