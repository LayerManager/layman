    <maplayer wkbType="{wkb_type}" refreshOnNotifyMessage="" simplifyDrawingHints="1" autoRefreshEnabled="0" simplifyDrawingTol="1" simplifyMaxScale="1" minScale="100000000" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" labelsEnabled="0" type="vector" autoRefreshTime="0" styleCategories="AllStyleCategories" readOnly="0" maxScale="0" simplifyLocal="1" geometry="{geometry_type}" refreshOnNotifyEnabled="0">
      <extent>
        {extent}
      </extent>
      <id>{layer_name}_{layer_uuid}</id>
      <datasource>dbname='{db_name}' host={db_host} port={db_port} user='{db_user}' password='{db_password}' sslmode=disable key='ogc_fid' srid=3857 type={layer_type} checkPrimaryKeyUnicity='1' table="{db_schema}"."{db_table}" (wkb_geometry)</datasource>
      <keywordList>
        <value></value>
      </keywordList>
      <layername>{layer_name}</layername>
      <srs>
        <spatialrefsys>
          <wkt>PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs"],AUTHORITY["EPSG","3857"]]</wkt>
          <proj4>+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs</proj4>
          <srsid>3857</srsid>
          <srid>3857</srid>
          <authid>EPSG:3857</authid>
          <description>WGS 84 / Pseudo-Mercator</description>
          <projectionacronym>merc</projectionacronym>
          <ellipsoidacronym>WGS84</ellipsoidacronym>
          <geographicflag>false</geographicflag>
        </spatialrefsys>
      </srs>
      <resourceMetadata>
        <identifier></identifier>
        <parentidentifier></parentidentifier>
        <language></language>
        <type>dataset</type>
        <title></title>
        <abstract></abstract>
        <links/>
        <fees></fees>
        <encoding></encoding>
        <crs>
          <spatialrefsys>
            <wkt>PROJCS["WGS 84 / Pseudo-Mercator",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]],PROJECTION["Mercator_1SP"],PARAMETER["central_meridian",0],PARAMETER["scale_factor",1],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["X",EAST],AXIS["Y",NORTH],EXTENSION["PROJ4","+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs"],AUTHORITY["EPSG","3857"]]</wkt>
            <proj4>+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs</proj4>
            <srsid>3857</srsid>
            <srid>3857</srid>
            <authid>EPSG:3857</authid>
            <description>WGS 84 / Pseudo-Mercator</description>
            <projectionacronym>merc</projectionacronym>
            <ellipsoidacronym>WGS84</ellipsoidacronym>
            <geographicflag>false</geographicflag>
          </spatialrefsys>
        </crs>
        <extent/>
      </resourceMetadata>
      <provider encoding="">postgres</provider>
      <vectorjoins/>
      <layerDependencies/>
      <dataDependencies/>
      <legend type="default-vector"/>
      <expressionfields/>
      <map-layer-style-manager current="default">
        <map-layer-style name="default"/>
      </map-layer-style-manager>
      <auxiliaryLayer/>
    </maplayer>
