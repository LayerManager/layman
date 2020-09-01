from multiprocessing import Process
import requests
import time
from flask import url_for
import pytest

import sys
import os

del sys.modules['layman']

from layman import app as app
from layman import settings
from layman.layer.rest_test import wait_till_ready


@pytest.fixture(scope="module")
def client():
    # print('before app.test_client()')
    client = app.test_client()

    # print('before Process(target=app.run, kwargs={...')
    server = Process(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': settings.LAYMAN_SERVER_NAME.split(':')[1],
        'debug': False,
    })
    # print('before server.start()')
    server.start()
    time.sleep(1)

    app.config['TESTING'] = True
    app.config['DEBUG'] = True
    app.config['SERVER_NAME'] = settings.LAYMAN_SERVER_NAME
    app.config['SESSION_COOKIE_DOMAIN'] = settings.LAYMAN_SERVER_NAME

    yield client

    server.terminate()
    server.join()


@pytest.fixture()
def app_context():
    with app.app_context() as ctx:
        yield ctx


@pytest.mark.usefixtures('app_context')
def test_rest_get(client):
    username = 'wfs_proxy_test'
    layername = 'layer_wfs_proxy_test'
    rest_path = url_for('rest_layers.post', username=username)
    file_paths = [
        'tmp/naturalearth/110m/cultural/ne_110m_populated_places.geojson',
    ]
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        files = [(open(fp, 'rb'), os.path.basename(fp)) for fp in file_paths]
        rv = client.post(rest_path, data={
            'file': files,
            'name': layername
        })
        assert rv.status_code == 200
    finally:
        for fp in files:
            fp[0].close()

    wait_till_ready(username, layername)

    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest/wfs-proxy"
    headers = {
        'Accept': 'text/xml',
        'Content-type': 'text/xml',
    }

    data_xml = f'''<?xml version="1.0"?>
    <wfs:Transaction
       version="2.0.0"
       service="WFS"
       xmlns:{username}="http://{username}"
       xmlns:fes="http://www.opengis.net/fes/2.0"
       xmlns:gml="http://www.opengis.net/gml/3.2"
       xmlns:wfs="http://www.opengis.net/wfs/2.0"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                           http://schemas.opengis.net/wfs/2.0/wfs.xsd
                           http://www.opengis.net/gml/3.2
                           http://schemas.opengis.net/gml/3.2.1/gml.xsd">
       <wfs:Insert>
           <{username}:{layername}>
               <{username}:wkb_geometry>
                   <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                       <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
                   </gml:Point>
               </{username}:wkb_geometry>
           </{username}:{layername}>
       </wfs:Insert>
    </wfs:Transaction>'''

    r = requests.get(rest_url,
                     data=data_xml,
                     headers=headers)
    assert r.status_code == 200
