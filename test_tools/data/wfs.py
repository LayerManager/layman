def get_wfs20_insert_points(geoserver_workspace, geoserver_layername):
    return f'''<?xml version="1.0"?>
        <wfs:Transaction
           version="2.0.0"
           service="WFS"
           xmlns:{geoserver_workspace}="http://{geoserver_workspace}"
           xmlns:fes="http://www.opengis.net/fes/2.0"
           xmlns:gml="http://www.opengis.net/gml/3.2"
           xmlns:wfs="http://www.opengis.net/wfs/2.0"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                               http://schemas.opengis.net/wfs/2.0/wfs.xsd
                               http://www.opengis.net/gml/3.2
                               http://schemas.opengis.net/gml/3.2.1/gml.xsd">
           <wfs:Insert>
               <{geoserver_workspace}:{geoserver_layername}>
                   <{geoserver_workspace}:wkb_geometry>
                       <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                           <gml:pos>1571000 6268800</gml:pos>
                       </gml:Point>
                   </{geoserver_workspace}:wkb_geometry>
               </{geoserver_workspace}:{geoserver_layername}>
           </wfs:Insert>
        </wfs:Transaction>'''


def get_wfs20_delete_point(geoserver_workspace, geoserver_layername):
    return f'''<?xml version="1.0"?>
        <wfs:Transaction
           version="2.0.0"
           service="WFS"
           xmlns:{geoserver_workspace}="http://{geoserver_workspace}"
           xmlns:fes="http://www.opengis.net/fes/2.0"
           xmlns:gml="http://www.opengis.net/gml/3.2"
           xmlns:wfs="http://www.opengis.net/wfs/2.0"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                               http://schemas.opengis.net/wfs/2.0/wfs.xsd
                               http://www.opengis.net/gml/3.2
                               http://schemas.opengis.net/gml/3.2.1/gml.xsd">
           <wfs:Delete typeName="{geoserver_workspace}:{geoserver_layername}">
                <fes:Intersects>
                    <fes:ValueReference>{geoserver_workspace}:wkb_geometry</fes:ValueReference>
                    <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                        <gml:pos>1571000 6268800</gml:pos>
                    </gml:Point>
                </fes:Intersects>
           </wfs:Delete>
        </wfs:Transaction>'''


def get_wfs20_insert_lines(geoserver_workspace, geoserver_layername):
    return f'''<?xml version="1.0"?>
    <wfs:Transaction
       version="2.0.0"
       service="WFS"
       xmlns:{geoserver_workspace}="http://{geoserver_workspace}"
       xmlns:fes="http://www.opengis.net/fes/2.0"
       xmlns:gml="http://www.opengis.net/gml/3.2"
       xmlns:wfs="http://www.opengis.net/wfs/2.0"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                           http://schemas.opengis.net/wfs/2.0/wfs.xsd
                           http://www.opengis.net/gml/3.2
                           http://schemas.opengis.net/gml/3.2.1/gml.xsd">
       <wfs:Insert>
           <{geoserver_workspace}:{geoserver_layername}>
               <{geoserver_workspace}:wkb_geometry>
                   <gml:MultiCurve srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                       <gml:curveMember>
                           <gml:LineString>
                               <gml:posList>3722077.1689 5775850.1007 3751406.9331 5815606.0102 3830548.3984 5781176.5357
                                   3866350.4899 5774848.8358 3880796.9478 5743277.797 3897591.3679 5738418.6547
                               </gml:posList>
                           </gml:LineString>
                       </gml:curveMember>
                   </gml:MultiCurve>
               </{geoserver_workspace}:wkb_geometry>
           </{geoserver_workspace}:{geoserver_layername}>
       </wfs:Insert>
    </wfs:Transaction>'''


def get_wfs20_insert_points_new_attr(geoserver_workspace, geoserver_layername, attr_names):
    attr_xml = ' '.join([
        f"<{geoserver_workspace}:{attr_name}>some value</{geoserver_workspace}:{attr_name}>"
        for attr_name in attr_names
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="2.0.0"
   service="WFS"
   xmlns:{geoserver_workspace}="http://{geoserver_workspace}"
   xmlns:fes="http://www.opengis.net/fes/2.0"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs/2.0"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                       http://schemas.opengis.net/wfs/2.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Insert>
       <{geoserver_workspace}:{geoserver_layername}>
           <{geoserver_workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
               </gml:Point>
           </{geoserver_workspace}:wkb_geometry>
           <{geoserver_workspace}:name>New name</{geoserver_workspace}:name>
           <{geoserver_workspace}:labelrank>3</{geoserver_workspace}:labelrank>
           {attr_xml}
       </{geoserver_workspace}:{geoserver_layername}>
   </wfs:Insert>
   <wfs:Insert>
       <{geoserver_workspace}:{geoserver_layername}>
           <{geoserver_workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.42108004308E7 2678415.5977</gml:pos>
               </gml:Point>
           </{geoserver_workspace}:wkb_geometry>
           <{geoserver_workspace}:name>New name2</{geoserver_workspace}:name>
           <{geoserver_workspace}:labelrank>4</{geoserver_workspace}:labelrank>
           {attr_xml}
       </{geoserver_workspace}:{geoserver_layername}>
   </wfs:Insert>
</wfs:Transaction>'''


def get_wfs10_insert_points_new_attr(geoserver_workspace, geoserver_layername, attr_names):
    attr_xml = ' '.join([
        f"<{geoserver_workspace}:{attr_name}>some value</{geoserver_workspace}:{attr_name}>"
        for attr_name in attr_names
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="1.0.0"
   service="WFS"
   xmlns:{geoserver_workspace}="http://{geoserver_workspace}"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs
                       http://schemas.opengis.net/wfs/1.0.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Insert>
       <{geoserver_workspace}:{geoserver_layername}>
           <{geoserver_workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
               </gml:Point>
           </{geoserver_workspace}:wkb_geometry>
           <{geoserver_workspace}:name>New name</{geoserver_workspace}:name>
           <{geoserver_workspace}:labelrank>3</{geoserver_workspace}:labelrank>
           {attr_xml}
       </{geoserver_workspace}:{geoserver_layername}>
   </wfs:Insert>
</wfs:Transaction>'''


def get_wfs11_insert_points_new_attr(geoserver_workspace, geoserver_layername, attr_names):
    attr_xml = ' '.join([
        f"<{geoserver_workspace}:{attr_name}>some value</{geoserver_workspace}:{attr_name}>"
        for attr_name in attr_names
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="1.1.0"
   service="WFS"
   xmlns:{geoserver_workspace}="http://{geoserver_workspace}"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs
                       http://schemas.opengis.net/wfs/1.1.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Insert>
       <{geoserver_workspace}:{geoserver_layername}>
           <{geoserver_workspace}:wkb_geometry>
           <gml:MultiLineString srsName="http://www.opengis.net/gml/srs/epsg.xml#3857">
               <gml:lineStringMember>
                   <gml:LineString>
                       <gml:coordinates decimal="." cs="," ts=" ">
   494475.71056415,5433016.8189323 494982.70115662,5435041.95096618
                       </gml:coordinates>
                   </gml:LineString>
               </gml:lineStringMember>
           </gml:MultiLineString>
           </{geoserver_workspace}:wkb_geometry>
           <{geoserver_workspace}:name>New name</{geoserver_workspace}:name>
           <{geoserver_workspace}:labelrank>3</{geoserver_workspace}:labelrank>
           {attr_xml}
       </{geoserver_workspace}:{geoserver_layername}>
   </wfs:Insert>
</wfs:Transaction>'''


def get_wfs11_insert_polygon_new_attr(geoserver_workspace, geoserver_layername, attr_names):
    attr_xml = ' '.join([
        f"<{attr_name}>some value</{attr_name}>"
        for attr_name in attr_names
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="1.1.0"
   service="WFS"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs
                       http://schemas.opengis.net/wfs/1.1.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Insert>
       <{geoserver_layername} xmlns="http://{geoserver_workspace}">
           <wkb_geometry>
           <gml:MultiLineString srsName="http://www.opengis.net/gml/srs/epsg.xml#3857">
               <gml:lineStringMember>
                   <gml:LineString>
                       <gml:coordinates decimal="." cs="," ts=" ">
   494475.71056415,5433016.8189323 494982.70115662,5435041.95096618
                       </gml:coordinates>
                   </gml:LineString>
               </gml:lineStringMember>
           </gml:MultiLineString>
           </wkb_geometry>
           <name>New name</name>
           <labelrank>3</labelrank>
           {attr_xml}
       </{geoserver_layername}>
   </wfs:Insert>
</wfs:Transaction>'''


def get_wfs20_update_points_new_attr(
        geoserver_workspace,
        geoserver_layername,
        attr_names,
        with_attr_namespace=False,
        with_filter=False,
):
    attr_prefix = f"{geoserver_workspace}:" if with_attr_namespace else ''
    attr_xml = ' '.join([
        f"""<wfs:Property>
               <wfs:ValueReference>{attr_prefix}{attr_name}</wfs:ValueReference>
               <wfs:Value>some value</wfs:Value>
           </wfs:Property>"""
        for attr_name in attr_names
    ])
    filter_xml = f"""<fes:Filter>
              <fes:ResourceId rid="{geoserver_layername}.1"/>
           </fes:Filter>
    """ if with_filter else ''
    return f'''<?xml version="1.0"?>
    <wfs:Transaction
       version="2.0.0"
       service="WFS"
       xmlns:{geoserver_workspace}="http://{geoserver_workspace}"
       xmlns:fes="http://www.opengis.net/fes/2.0"
       xmlns:gml="http://www.opengis.net/gml/3.2"
       xmlns:wfs="http://www.opengis.net/wfs/2.0"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                           http://schemas.opengis.net/wfs/2.0/wfs.xsd
                           http://www.opengis.net/gml/3.2
                           http://schemas.opengis.net/gml/3.2.1/gml.xsd">
       <wfs:Update typeName="{geoserver_workspace}:{geoserver_layername}">
           {attr_xml}
           {filter_xml}
       </wfs:Update>
    </wfs:Transaction>'''


def get_wfs10_update_points_new(
        geoserver_workspace,
        geoserver_layername,
        attr_names,
        with_attr_namespace=False,
        with_filter=False,
):
    attr_prefix = f"{geoserver_workspace}:" if with_attr_namespace else ''
    attr_xml = ' '.join([
        f"""<wfs:Property>
               <wfs:Name>{attr_prefix}{attr_name}</wfs:Name>
               <wfs:Value>some value</wfs:Value>
           </wfs:Property>"""
        for attr_name in attr_names
    ])
    filter_xml = f"""<ogc:Filter>
              <ogc:GmlObjectId gml:id="{geoserver_layername}.1"/>
           </ogc:Filter>
    """ if with_filter else ''
    return f'''<?xml version="1.0"?>
    <wfs:Transaction
       version="1.0.0"
       service="WFS"
       xmlns:{geoserver_workspace}="http://{geoserver_workspace}"
       xmlns:gml="http://www.opengis.net/gml/3.2"
       xmlns:ogc="http://www.opengis.net/ogc"
       xmlns:wfs="http://www.opengis.net/wfs"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.opengis.net/wfs
                           http://schemas.opengis.net/wfs/1.0.0/wfs.xsd
                           http://www.opengis.net/gml/3.2
                           http://schemas.opengis.net/gml/3.2.1/gml.xsd">
       <wfs:Update typeName="{geoserver_workspace}:{geoserver_layername}">
           {attr_xml}
           {filter_xml}
       </wfs:Update>
    </wfs:Transaction>'''


def get_wfs20_replace_points_new_attr(geoserver_workspace, geoserver_layername, attr_names):
    attr_xml = ' '.join([
        f"<{geoserver_workspace}:{attr_name}>some value</{geoserver_workspace}:{attr_name}>"
        for attr_name in attr_names
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="2.0.0"
   service="WFS"
   xmlns:{geoserver_workspace}="http://{geoserver_workspace}"
   xmlns:fes="http://www.opengis.net/fes/2.0"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs/2.0"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                       http://schemas.opengis.net/wfs/2.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Replace>
       <{geoserver_workspace}:{geoserver_layername}>
           <{geoserver_workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
               </gml:Point>
           </{geoserver_workspace}:wkb_geometry>
           <{geoserver_workspace}:name>New name</{geoserver_workspace}:name>
           <{geoserver_workspace}:labelrank>3</{geoserver_workspace}:labelrank>
           {attr_xml}
       </{geoserver_workspace}:{geoserver_layername}>
       <fes:Filter>
          <fes:ResourceId rid="{geoserver_layername}.1"/>
       </fes:Filter>
   </wfs:Replace>
   <wfs:Replace>
       <{geoserver_workspace}:{geoserver_layername}>
           <{geoserver_workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.42108004308E7 2678415.5977</gml:pos>
               </gml:Point>
           </{geoserver_workspace}:wkb_geometry>
           <{geoserver_workspace}:name>New name2</{geoserver_workspace}:name>
           <{geoserver_workspace}:labelrank>4</{geoserver_workspace}:labelrank>
           {attr_xml}
       </{geoserver_workspace}:{geoserver_layername}>
       <fes:Filter>
          <fes:ResourceId rid="{geoserver_layername}.2"/>
       </fes:Filter>
   </wfs:Replace>
</wfs:Transaction>'''


def get_wfs20_complex_new_attr(geoserver_workspace,
                               geoserver_layername1,
                               geoserver_layername2,
                               attr_names_insert1,
                               attr_names_insert2,
                               attr_names_update,
                               attr_names_replace):
    with_attr_namespace = True
    attr_xml_insert1 = ' '.join([
        f"<{geoserver_workspace}:{attr_name}>some value</{geoserver_workspace}:{attr_name}>"
        for attr_name in attr_names_insert1
    ])
    attr_xml_insert2 = ' '.join([
        f"<{geoserver_workspace}:{attr_name}>some value</{geoserver_workspace}:{attr_name}>"
        for attr_name in attr_names_insert2
    ])
    attr_prefix = f"{geoserver_workspace}:" if with_attr_namespace else ''
    attr_xml_update = ' '.join([
        f"""<wfs:Property>
               <wfs:ValueReference>{attr_prefix}{attr_name}</wfs:ValueReference>
               <wfs:Value>some value</wfs:Value>
           </wfs:Property>"""
        for attr_name in attr_names_update
    ])
    attr_xml_replace = ' '.join([
        f"<{geoserver_workspace}:{attr_name}>some value</{geoserver_workspace}:{attr_name}>"
        for attr_name in attr_names_replace
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="2.0.0"
   service="WFS"
   xmlns:{geoserver_workspace}="http://{geoserver_workspace}"
   xmlns:fes="http://www.opengis.net/fes/2.0"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs/2.0"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                       http://schemas.opengis.net/wfs/2.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Insert>
       <{geoserver_workspace}:{geoserver_layername1}>
           <{geoserver_workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
               </gml:Point>
           </{geoserver_workspace}:wkb_geometry>
           <{geoserver_workspace}:name>New name</{geoserver_workspace}:name>
           <{geoserver_workspace}:labelrank>3</{geoserver_workspace}:labelrank>
           {attr_xml_insert1}
       </{geoserver_workspace}:{geoserver_layername1}>
       <{geoserver_workspace}:{geoserver_layername2}>
           <{geoserver_workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.42108004308E7 2678415.5977</gml:pos>
               </gml:Point>
           </{geoserver_workspace}:wkb_geometry>
           <{geoserver_workspace}:name>New name2</{geoserver_workspace}:name>
           <{geoserver_workspace}:labelrank>4</{geoserver_workspace}:labelrank>
           {attr_xml_insert2}
       </{geoserver_workspace}:{geoserver_layername2}>
   </wfs:Insert>
   <wfs:Update typeName="{geoserver_workspace}:{geoserver_layername2}">
       {attr_xml_update}
   </wfs:Update>
   <wfs:Replace>
       <{geoserver_workspace}:{geoserver_layername1}>
           <{geoserver_workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
               </gml:Point>
           </{geoserver_workspace}:wkb_geometry>
           <{geoserver_workspace}:name>New name</{geoserver_workspace}:name>
           <{geoserver_workspace}:labelrank>3</{geoserver_workspace}:labelrank>
           {attr_xml_replace}
       </{geoserver_workspace}:{geoserver_layername1}>
       <fes:Filter>
          <fes:ResourceId rid="{geoserver_layername1}.1"/>
       </fes:Filter>
   </wfs:Replace>
</wfs:Transaction>'''


def get_wfs11_implicit_ns_update():
    return '''<Transaction xmlns="http://www.opengis.net/wfs" service="WFS" version="1.1.0"
  xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Update typeName="filip:poly" xmlns:filip="http://filip">
    <Property>
      <Name>wkb_geometry</Name>
      <Value>
        <Polygon xmlns="http://www.opengis.net/gml" srsName="EPSG:3857">
          <exterior>
            <LinearRing srsName="EPSG:3857">
              <posList srsDimension="2">1766017.811 11424089.3044 -2106309.2073 3245917.4174 2674829.2541 3522473.9546
                4613901.549156107 6717360.945902297 4492452.1402 11187040.8439 1766017.811 11424089.3044</posList>
            </LinearRing>
          </exterior>
        </Polygon>
      </Value>
    </Property>
    <Filter xmlns="http://www.opengis.net/ogc">
      <FeatureId fid="poly.1" />
    </Filter>
  </Update>
</Transaction>'''


def get_wfs2_implicit_ns_update():
    return '''<Transaction xmlns="http://www.opengis.net/wfs" service="WFS" version="2.0.0"
  xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <Update typeName="filip:poly" xmlns:filip="http://filip">
    <Property>
      <ValueReference>wkb_geometry</ValueReference>
      <Value>
        <Polygon xmlns="http://www.opengis.net/gml" srsName="EPSG:3857">
          <exterior>
            <LinearRing srsName="EPSG:3857">
              <posList srsDimension="2">1766017.811 11424089.3044 -2106309.2073 3245917.4174 2674829.2541 3522473.9546
                4613901.549156107 6717360.945902297 4492452.1402 11187040.8439 1766017.811 11424089.3044</posList>
            </LinearRing>
          </exterior>
        </Polygon>
      </Value>
    </Property>
    <Filter xmlns="http://www.opengis.net/ogc">
      <FeatureId fid="poly.1" />
    </Filter>
  </Update>
</Transaction>'''


def get_wfs1_implicit_ns_delete():
    return '''<Transaction xmlns="http://www.opengis.net/wfs" service="WFS" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Delete typeName="filip:europa_5514"
        xmlns:filip="http://filip">
        <Filter xmlns="http://www.opengis.net/ogc">
            <FeatureId fid="europa_5514.8"/>
        </Filter>
    </Delete>
</Transaction>'''


def get_wfs1_implicit_ns_insert():
    return '''<Transaction xmlns="http://www.opengis.net/wfs" service="WFS" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <Insert>
        <europa_5514 xmlns="http://filip" fid="europa_5514.6">
            <name>Poland</name>
            <featurecla>Admin-0 country</featurecla>
            <scalerank>1</scalerank>
            <labelrank>3</labelrank>
            <sovereignt>Poland - edited</sovereignt>
            <wkb_geometry>
                <Polygon xmlns="http://www.opengis.net/gml" srsName="EPSG:3857">
                    <exterior>
                        <LinearRing srsName="EPSG:3857">
                            <posList srsDimension="2">2614211.3651 7153629.9962 2619046.8052 7070463.4035 2649929.6652 6999641.6022 2649293.9241 6926090.8192 2582536.0408 6888685.9562 2616882.4216 6804428.1478 2619008.127 6724286.0382 2674998.4235 6569374.6514 2663063.4952 6520211.3403 2607821.7186 6499899.7148 2506741.6935 6356169.7269 2535461.5251 6279530.8739 2511162.08 6289440.8626 2405368.9686 6355024.0634 2325235.7895 6330844.9667 2272679.2096 6348400.3781 2206910.8099 6311791.8642 2150768.8287 6372414.4127 2105001.8373 6349146.2174 2098719.6077 6359489.0404 2047483.7377 6444309.7435 1964720.4814 6454772.7617 1954156.6924 6509230.7607 1877813.0448 6528765.0311 1861195.4001 6483719.8167 1800722.6293 6519782.3977 1807664.2538 6567993.8629 1724434.9305 6583294.4294 1671669.8951 6640174.5528 1626035.9364 6754170.8925 1634708.5062 6816394.1479 1607161.2921 6913892.4306 1566740.9467 6979519.1318 1597774.3249 7029023.1742 1571763.0525 7124261.0145 1647816.0606 7179755.323 1821535.6031 7267944.9442 1961724.1941 7333108.5554 2072825.8228 7300515.9271 2081220.7716 7253693.7653 2188576.2862 7251279.9765 2325679.4523 7229585.6542 2530380.9019 7232458.9747 2587476.5871 7212067.7144 2614211.3651 7153629.9962</posList>
                        </LinearRing>
                    </exterior>
                </Polygon>
            </wkb_geometry>
        </europa_5514>
    </Insert>
</Transaction>'''
