def get_wfs20_insert_points(workspace, layername):
    return f'''<?xml version="1.0"?>
        <wfs:Transaction
           version="2.0.0"
           service="WFS"
           xmlns:{workspace}="http://{workspace}"
           xmlns:fes="http://www.opengis.net/fes/2.0"
           xmlns:gml="http://www.opengis.net/gml/3.2"
           xmlns:wfs="http://www.opengis.net/wfs/2.0"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                               http://schemas.opengis.net/wfs/2.0/wfs.xsd
                               http://www.opengis.net/gml/3.2
                               http://schemas.opengis.net/gml/3.2.1/gml.xsd">
           <wfs:Insert>
               <{workspace}:{layername}>
                   <{workspace}:wkb_geometry>
                       <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                           <gml:pos>1571000 6268800</gml:pos>
                       </gml:Point>
                   </{workspace}:wkb_geometry>
               </{workspace}:{layername}>
           </wfs:Insert>
        </wfs:Transaction>'''


def get_wfs20_delete_point(workspace, layername):
    return f'''<?xml version="1.0"?>
        <wfs:Transaction
           version="2.0.0"
           service="WFS"
           xmlns:{workspace}="http://{workspace}"
           xmlns:fes="http://www.opengis.net/fes/2.0"
           xmlns:gml="http://www.opengis.net/gml/3.2"
           xmlns:wfs="http://www.opengis.net/wfs/2.0"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                               http://schemas.opengis.net/wfs/2.0/wfs.xsd
                               http://www.opengis.net/gml/3.2
                               http://schemas.opengis.net/gml/3.2.1/gml.xsd">
           <wfs:Delete typeName="{workspace}:{layername}">
                <fes:Intersects>
                    <fes:ValueReference>{workspace}:wkb_geometry</fes:ValueReference>
                    <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                        <gml:pos>1571000 6268800</gml:pos>
                    </gml:Point>
                </fes:Intersects>
           </wfs:Delete>
        </wfs:Transaction>'''


def get_wfs20_insert_lines(workspace, layername):
    return f'''<?xml version="1.0"?>
    <wfs:Transaction
       version="2.0.0"
       service="WFS"
       xmlns:{workspace}="http://{workspace}"
       xmlns:fes="http://www.opengis.net/fes/2.0"
       xmlns:gml="http://www.opengis.net/gml/3.2"
       xmlns:wfs="http://www.opengis.net/wfs/2.0"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                           http://schemas.opengis.net/wfs/2.0/wfs.xsd
                           http://www.opengis.net/gml/3.2
                           http://schemas.opengis.net/gml/3.2.1/gml.xsd">
       <wfs:Insert>
           <{workspace}:{layername}>
               <{workspace}:wkb_geometry>
                   <gml:MultiCurve srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                       <gml:curveMember>
                           <gml:LineString>
                               <gml:posList>3722077.1689 5775850.1007 3751406.9331 5815606.0102 3830548.3984 5781176.5357
                                   3866350.4899 5774848.8358 3880796.9478 5743277.797 3897591.3679 5738418.6547
                               </gml:posList>
                           </gml:LineString>
                       </gml:curveMember>
                   </gml:MultiCurve>
               </{workspace}:wkb_geometry>
           </{workspace}:{layername}>
       </wfs:Insert>
    </wfs:Transaction>'''


def get_wfs20_insert_points_new_attr(workspace, layername, attr_names):
    attr_xml = ' '.join([
        f"<{workspace}:{attr_name}>some value</{workspace}:{attr_name}>"
        for attr_name in attr_names
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="2.0.0"
   service="WFS"
   xmlns:{workspace}="http://{workspace}"
   xmlns:fes="http://www.opengis.net/fes/2.0"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs/2.0"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                       http://schemas.opengis.net/wfs/2.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Insert>
       <{workspace}:{layername}>
           <{workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
               </gml:Point>
           </{workspace}:wkb_geometry>
           <{workspace}:name>New name</{workspace}:name>
           <{workspace}:labelrank>3</{workspace}:labelrank>
           {attr_xml}
       </{workspace}:{layername}>
   </wfs:Insert>
   <wfs:Insert>
       <{workspace}:{layername}>
           <{workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.42108004308E7 2678415.5977</gml:pos>
               </gml:Point>
           </{workspace}:wkb_geometry>
           <{workspace}:name>New name2</{workspace}:name>
           <{workspace}:labelrank>4</{workspace}:labelrank>
           {attr_xml}
       </{workspace}:{layername}>
   </wfs:Insert>
</wfs:Transaction>'''


def get_wfs10_insert_points_new_attr(workspace, layername, attr_names):
    attr_xml = ' '.join([
        f"<{workspace}:{attr_name}>some value</{workspace}:{attr_name}>"
        for attr_name in attr_names
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="1.0.0"
   service="WFS"
   xmlns:{workspace}="http://{workspace}"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs
                       http://schemas.opengis.net/wfs/1.0.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Insert>
       <{workspace}:{layername}>
           <{workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
               </gml:Point>
           </{workspace}:wkb_geometry>
           <{workspace}:name>New name</{workspace}:name>
           <{workspace}:labelrank>3</{workspace}:labelrank>
           {attr_xml}
       </{workspace}:{layername}>
   </wfs:Insert>
</wfs:Transaction>'''


def get_wfs11_insert_points_new_attr(workspace, layername, attr_names):
    attr_xml = ' '.join([
        f"<{workspace}:{attr_name}>some value</{workspace}:{attr_name}>"
        for attr_name in attr_names
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="1.1.0"
   service="WFS"
   xmlns:{workspace}="http://{workspace}"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs
                       http://schemas.opengis.net/wfs/1.1.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Insert>
       <{workspace}:{layername}>
           <{workspace}:wkb_geometry>
           <gml:MultiLineString srsName="http://www.opengis.net/gml/srs/epsg.xml#3857">
               <gml:lineStringMember>
                   <gml:LineString>
                       <gml:coordinates decimal="." cs="," ts=" ">
   494475.71056415,5433016.8189323 494982.70115662,5435041.95096618
                       </gml:coordinates>
                   </gml:LineString>
               </gml:lineStringMember>
           </gml:MultiLineString>
           </{workspace}:wkb_geometry>
           <{workspace}:name>New name</{workspace}:name>
           <{workspace}:labelrank>3</{workspace}:labelrank>
           {attr_xml}
       </{workspace}:{layername}>
   </wfs:Insert>
</wfs:Transaction>'''


def get_wfs11_insert_polygon_new_attr(workspace, layername, attr_names):
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
       <{layername} xmlns="http://{workspace}">
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
       </{layername}>
   </wfs:Insert>
</wfs:Transaction>'''


def get_wfs20_update_points_new_attr(
        workspace,
        layername,
        attr_names,
        with_attr_namespace=False,
        with_filter=False,
):
    attr_prefix = f"{workspace}:" if with_attr_namespace else ''
    attr_xml = ' '.join([
        f"""<wfs:Property>
               <wfs:ValueReference>{attr_prefix}{attr_name}</wfs:ValueReference>
               <wfs:Value>some value</wfs:Value>
           </wfs:Property>"""
        for attr_name in attr_names
    ])
    filter_xml = f"""<fes:Filter>
              <fes:ResourceId rid="{layername}.1"/>
           </fes:Filter>
    """ if with_filter else ''
    return f'''<?xml version="1.0"?>
    <wfs:Transaction
       version="2.0.0"
       service="WFS"
       xmlns:{workspace}="http://{workspace}"
       xmlns:fes="http://www.opengis.net/fes/2.0"
       xmlns:gml="http://www.opengis.net/gml/3.2"
       xmlns:wfs="http://www.opengis.net/wfs/2.0"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                           http://schemas.opengis.net/wfs/2.0/wfs.xsd
                           http://www.opengis.net/gml/3.2
                           http://schemas.opengis.net/gml/3.2.1/gml.xsd">
       <wfs:Update typeName="{workspace}:{layername}">
           {attr_xml}
           {filter_xml}
       </wfs:Update>
    </wfs:Transaction>'''


def get_wfs10_update_points_new(
        workspace,
        layername,
        attr_names,
        with_attr_namespace=False,
        with_filter=False,
):
    attr_prefix = f"{workspace}:" if with_attr_namespace else ''
    attr_xml = ' '.join([
        f"""<wfs:Property>
               <wfs:Name>{attr_prefix}{attr_name}</wfs:Name>
               <wfs:Value>some value</wfs:Value>
           </wfs:Property>"""
        for attr_name in attr_names
    ])
    filter_xml = f"""<ogc:Filter>
              <ogc:GmlObjectId gml:id="{layername}.1"/>
           </ogc:Filter>
    """ if with_filter else ''
    return f'''<?xml version="1.0"?>
    <wfs:Transaction
       version="1.0.0"
       service="WFS"
       xmlns:{workspace}="http://{workspace}"
       xmlns:gml="http://www.opengis.net/gml/3.2"
       xmlns:ogc="http://www.opengis.net/ogc"
       xmlns:wfs="http://www.opengis.net/wfs"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.opengis.net/wfs
                           http://schemas.opengis.net/wfs/1.0.0/wfs.xsd
                           http://www.opengis.net/gml/3.2
                           http://schemas.opengis.net/gml/3.2.1/gml.xsd">
       <wfs:Update typeName="{workspace}:{layername}">
           {attr_xml}
           {filter_xml}
       </wfs:Update>
    </wfs:Transaction>'''


def get_wfs20_replace_points_new_attr(workspace, layername, attr_names):
    attr_xml = ' '.join([
        f"<{workspace}:{attr_name}>some value</{workspace}:{attr_name}>"
        for attr_name in attr_names
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="2.0.0"
   service="WFS"
   xmlns:{workspace}="http://{workspace}"
   xmlns:fes="http://www.opengis.net/fes/2.0"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs/2.0"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                       http://schemas.opengis.net/wfs/2.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Replace>
       <{workspace}:{layername}>
           <{workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
               </gml:Point>
           </{workspace}:wkb_geometry>
           <{workspace}:name>New name</{workspace}:name>
           <{workspace}:labelrank>3</{workspace}:labelrank>
           {attr_xml}
       </{workspace}:{layername}>
       <fes:Filter>
          <fes:ResourceId rid="{layername}.1"/>
       </fes:Filter>
   </wfs:Replace>
   <wfs:Replace>
       <{workspace}:{layername}>
           <{workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.42108004308E7 2678415.5977</gml:pos>
               </gml:Point>
           </{workspace}:wkb_geometry>
           <{workspace}:name>New name2</{workspace}:name>
           <{workspace}:labelrank>4</{workspace}:labelrank>
           {attr_xml}
       </{workspace}:{layername}>
       <fes:Filter>
          <fes:ResourceId rid="{layername}.2"/>
       </fes:Filter>
   </wfs:Replace>
</wfs:Transaction>'''


def get_wfs20_complex_new_attr(workspace,
                               layername1,
                               layername2,
                               attr_names_insert1,
                               attr_names_insert2,
                               attr_names_update,
                               attr_names_replace):
    with_attr_namespace = True
    attr_xml_insert1 = ' '.join([
        f"<{workspace}:{attr_name}>some value</{workspace}:{attr_name}>"
        for attr_name in attr_names_insert1
    ])
    attr_xml_insert2 = ' '.join([
        f"<{workspace}:{attr_name}>some value</{workspace}:{attr_name}>"
        for attr_name in attr_names_insert2
    ])
    attr_prefix = f"{workspace}:" if with_attr_namespace else ''
    attr_xml_update = ' '.join([
        f"""<wfs:Property>
               <wfs:ValueReference>{attr_prefix}{attr_name}</wfs:ValueReference>
               <wfs:Value>some value</wfs:Value>
           </wfs:Property>"""
        for attr_name in attr_names_update
    ])
    attr_xml_replace = ' '.join([
        f"<{workspace}:{attr_name}>some value</{workspace}:{attr_name}>"
        for attr_name in attr_names_replace
    ])
    return f'''<?xml version="1.0"?>
<wfs:Transaction
   version="2.0.0"
   service="WFS"
   xmlns:{workspace}="http://{workspace}"
   xmlns:fes="http://www.opengis.net/fes/2.0"
   xmlns:gml="http://www.opengis.net/gml/3.2"
   xmlns:wfs="http://www.opengis.net/wfs/2.0"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xsi:schemaLocation="http://www.opengis.net/wfs/2.0
                       http://schemas.opengis.net/wfs/2.0/wfs.xsd
                       http://www.opengis.net/gml/3.2
                       http://schemas.opengis.net/gml/3.2.1/gml.xsd">
   <wfs:Insert>
       <{workspace}:{layername1}>
           <{workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
               </gml:Point>
           </{workspace}:wkb_geometry>
           <{workspace}:name>New name</{workspace}:name>
           <{workspace}:labelrank>3</{workspace}:labelrank>
           {attr_xml_insert1}
       </{workspace}:{layername1}>
       <{workspace}:{layername2}>
           <{workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.42108004308E7 2678415.5977</gml:pos>
               </gml:Point>
           </{workspace}:wkb_geometry>
           <{workspace}:name>New name2</{workspace}:name>
           <{workspace}:labelrank>4</{workspace}:labelrank>
           {attr_xml_insert2}
       </{workspace}:{layername2}>
   </wfs:Insert>
   <wfs:Update typeName="{workspace}:{layername2}">
       {attr_xml_update}
   </wfs:Update>
   <wfs:Replace>
       <{workspace}:{layername1}>
           <{workspace}:wkb_geometry>
               <gml:Point srsName="urn:ogc:def:crs:EPSG::3857" srsDimension="2">
                   <gml:pos>1.27108004304E7 2548415.5977</gml:pos>
               </gml:Point>
           </{workspace}:wkb_geometry>
           <{workspace}:name>New name</{workspace}:name>
           <{workspace}:labelrank>3</{workspace}:labelrank>
           {attr_xml_replace}
       </{workspace}:{layername1}>
       <fes:Filter>
          <fes:ResourceId rid="{layername1}.1"/>
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
