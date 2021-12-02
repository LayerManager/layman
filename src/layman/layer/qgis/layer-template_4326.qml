<maplayer wkbType="{wkb_type}" refreshOnNotifyMessage="" simplifyDrawingHints="1" autoRefreshEnabled="0" simplifyDrawingTol="1"
          simplifyMaxScale="1" minScale="100000000" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" labelsEnabled="0" type="vector"
          autoRefreshTime="0" styleCategories="AllStyleCategories" readOnly="0" maxScale="0" simplifyLocal="1" geometry="{qml_geometry}"
          refreshOnNotifyEnabled="0">
    <extent>
        {extent}
    </extent>
    <id>{layer_name}_{layer_uuid}</id>
    <datasource>dbname='{db_name}' host={db_host} port={db_port} user='{db_user}' password='{db_password}' sslmode=disable key='ogc_fid'
        srid=4326 type={source_type} checkPrimaryKeyUnicity='1' table="{db_schema}"."{db_table}" (wkb_geometry)
    </datasource>
    <keywordList>
        <value></value>
    </keywordList>
    <layername>{layer_name}</layername>
    <srs>
        <spatialrefsys>
            <wkt>GEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS
                84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],CS[ellipsoidal,2],AXIS["geodetic
                latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],AXIS["geodetic longitude
                (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]],USAGE[SCOPE["unknown"],AREA["World"],BBOX[-90,-180,90,180]],ID["EPSG",4326]]
            </wkt>
            <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
            <srsid>3452</srsid>
            <srid>4326</srid>
            <authid>EPSG:4326</authid>
            <description>WGS 84</description>
            <projectionacronym>longlat</projectionacronym>
            <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
            <geographicflag>true</geographicflag>
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
                <wkt>GEOGCRS["WGS 84",DATUM["World Geodetic System 1984",ELLIPSOID["WGS
                    84",6378137,298.257223563,LENGTHUNIT["metre",1]]],PRIMEM["Greenwich",0,ANGLEUNIT["degree",0.0174532925199433]],CS[ellipsoidal,2],AXIS["geodetic
                    latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],AXIS["geodetic longitude
                    (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]],USAGE[SCOPE["unknown"],AREA["World"],BBOX[-90,-180,90,180]],ID["EPSG",4326]]
                </wkt>
                <proj4>+proj=longlat +datum=WGS84 +no_defs</proj4>
                <srsid>3452</srsid>
                <srid>4326</srid>
                <authid>EPSG:4326</authid>
                <description>WGS 84</description>
                <projectionacronym>longlat</projectionacronym>
                <ellipsoidacronym>EPSG:7030</ellipsoidacronym>
                <geographicflag>true</geographicflag>
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
