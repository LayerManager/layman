import base64
import re

from flask import Flask, request, redirect, jsonify

from .db import create_connection_cursor, ensure_user_schema, import_layer_vector_file
from .filesystem import get_safe_layername, \
    save_layer_files, check_layer_crs, ensure_user_dir
from .geoserver import ensure_user_workspace, publish_layer_from_db, \
    generate_layer_thumbnail
from .http import LaymanError
from .settings import *

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

@app.route('/')
def index():
    return redirect('/static/index.html')

@app.route('/rest/<username>/layers', methods=['POST'])
def post_layers(username):
    app.logger.info('upload_file')

    # USER
    username_re = r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"
    if not re.match(username_re, username):
        raise LaymanError(2, {'parameter': 'user', 'expected': username_re})
    if username in PG_NON_USER_SCHEMAS:
        raise LaymanError(8, {'schema': username})

    # FILE
    if 'file' not in request.files:
        raise LaymanError(1, {'parameter': 'file'})
    files = request.files.getlist("file")

    # NAME
    unsafe_layername = request.form.get('name', '')
    layername = get_safe_layername(unsafe_layername, files)

    # CRS
    crs_id = None
    if len(request.form.get('crs', '')) > 0:
        crs_id = request.form['crs']
        if crs_id not in INPUT_SRS_LIST:
            raise LaymanError(2, {'parameter': 'crs', 'supported_values':
                INPUT_SRS_LIST})
    check_crs = crs_id is None

    # TITLE
    if len(request.form.get('title', '')) > 0:
        title = request.form['title']
    else:
        title = layername

    # DESCRIPTION
    description = request.form.get('description', '')

    # SLD
    sld_file = None
    if 'sld' in request.files:
        sld_file = request.files['sld']

    # save files
    userdir = ensure_user_dir(username)
    main_filename = save_layer_files(username, layername, files)
    main_filepath = os.path.join(userdir, main_filename)
    if check_crs:
        check_layer_crs(main_filepath)

    # import into DB table
    conn_cur = create_connection_cursor()
    ensure_user_schema(username, conn_cur=conn_cur)
    import_layer_vector_file(username, layername, main_filepath, crs_id, conn_cur=conn_cur)

    # publish layer to GeoServer
    ensure_user_workspace(username)
    publish_layer_from_db(username, layername, description, title, sld_file)

    # generate thumbnail
    tn_img = generate_layer_thumbnail(username, layername)

    # return result
    wms_proxy_url = urljoin(LAYMAN_GS_PROXY_URL, username + '/ows')
    wfs_proxy_url = wms_proxy_url

    app.logger.info('uploaded layer '+layername)
    return jsonify({
        'file_name': main_filename,
        'table_name': layername,
        'layer_name': layername,
        'wms': wms_proxy_url,
        'wfs': wfs_proxy_url,
        'thumbnail': ("data:image/png;" +
                      "base64," + base64.b64encode(tn_img.read()).decode('utf-8')),
    }), 200


@app.errorhandler(LaymanError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.http_code
    return response