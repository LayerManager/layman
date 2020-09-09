import time
import requests
import os

from layman import settings


ISS_URL_HEADER = 'AuthorizationIssUrl'
TOKEN_HEADER = 'Authorization'

layer_keys_to_check = ['db_table', 'wms', 'wfs', 'thumbnail', 'file', 'metadata']


def wait_for_rest(url, max_attempts, sleeping_time, keys_to_check):
    r = requests.get(url)

    attempts = 1
    while not (r.status_code == 200 and all(
            'status' not in r.json()[k] for k in keys_to_check
    )):
        time.sleep(sleeping_time)
        r = requests.get(url)
        attempts += 1
        if attempts > max_attempts:
            raise Exception('Max attempts reached!')


def publish_layer(username, layername, file_paths, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"

    r_url = f"{rest_url}/{username}/layers"
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        r = requests.post(r_url, files=[
            ('file', (os.path.basename(fp), open(fp, 'rb')))
            for fp in file_paths
        ], data={
            'name': layername,
        }, headers=headers)
        assert r.status_code == 200, r.text
    finally:
        for fp in files:
            fp[0].close()

    wait_for_rest(f"{rest_url}/{username}/layers/{layername}", 20, 0.5, layer_keys_to_check)
    return layername


def patch_layer(username, layername, file_paths, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"

    r_url = f"{rest_url}/{username}/layers/{layername}"
    for fp in file_paths:
        assert os.path.isfile(fp)
    files = []
    try:
        r = requests.patch(r_url, files=[
            ('file', (os.path.basename(fp), open(fp, 'rb')))
            for fp in file_paths
        ], headers=headers)
        assert r.status_code == 200, r.text
    finally:
        for fp in files:
            fp[0].close()

    wait_for_rest(f"{rest_url}/{username}/layers/{layername}", 20, 0.5, layer_keys_to_check)
    return layername


def delete_layer(username, layername, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"

    r_url = f"{rest_url}/{username}/layers/{layername}"
    r = requests.delete(r_url, headers=headers)
    assert r.status_code == 200, r.text


def assert_user_layers(username, layernames):
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/{username}/layers"
    r = requests.get(r_url)
    assert r.status_code == 200, f"r.status_code={r.status_code}\n{r.text}=r.text"
    layman_names = [li['name'] for li in r.json()]
    assert set(layman_names) == set(layernames), f"{r.text}=r.text"


def reserve_username(username, headers=None):
    headers = headers or {}
    rest_url = f"http://{settings.LAYMAN_SERVER_NAME}/rest"
    r_url = f"{rest_url}/current-user?adjust_username=true"
    r = requests.patch(r_url, headers=headers)
    assert r.status_code == 200, r.text
    claimed_username = r.json()['username']
    assert claimed_username == username


def get_wfs_insert_points(username, layername):
    return f'''<?xml version="1.0"?>
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


def get_wfs_insert_lines(username, layername):
    return f'''<?xml version="1.0"?>
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
                   <gml:MultiCurve srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                       <gml:curveMember>
                           <gml:LineString>
                               <gml:posList>3722077.1689 5775850.1007 3751406.9331 5815606.0102 3830548.3984 5781176.5357
                                   3866350.4899 5774848.8358 3880796.9478 5743277.797 3897591.3679 5738418.6547
                               </gml:posList>
                           </gml:LineString>
                       </gml:curveMember>
                   </gml:MultiCurve>
               </{username}:wkb_geometry>
           </{username}:{layername}>
       </wfs:Insert>
    </wfs:Transaction>'''


def get_wfs_insert_points_new_attr(username, layername, attr_name):
    return f'''<?xml version="1.0"?>
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
           <{username}:name>New name</{username}:name>
           <{username}:labelrank>3</{username}:labelrank>
           <{username}:{attr_name}>some value</{username}:{attr_name}>
       </{username}:{layername}>
   </wfs:Insert>
   <wfs:Insert>
       <{username}:{layername}>
           <{username}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.42108004308E7 2678415.5977</gml:pos>
               </gml:Point>
           </{username}:wkb_geometry>
           <{username}:name>New name2</{username}:name>
           <{username}:labelrank>4</{username}:labelrank>
           <{username}:{attr_name}>some value</{username}:{attr_name}>
       </{username}:{layername}>
   </wfs:Insert>
</wfs:Transaction>'''
