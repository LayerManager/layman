<maplayer wkbType="{wkb_type}" refreshOnNotifyMessage="" simplifyDrawingHints="1" autoRefreshEnabled="0" simplifyDrawingTol="1"
          simplifyMaxScale="1" minScale="100000000" hasScaleBasedVisibilityFlag="0" simplifyAlgorithm="0" labelsEnabled="0" type="vector"
          autoRefreshTime="0" styleCategories="AllStyleCategories" readOnly="0" maxScale="0" simplifyLocal="1" geometry="{qml_geometry}"
          refreshOnNotifyEnabled="0">
    <extent>
        {extent}
    </extent>
    <id>{layer_name}_{layer_uuid}</id>
    <datasource>dbname='{db_name}' host={db_host} port={db_port} user='{db_user}' password='{db_password}' sslmode=disable key='ogc_fid'
        srid={srid} type={source_type} checkPrimaryKeyUnicity='1' table="{db_schema}"."{db_table}" ({geo_column})
    </datasource>
    <keywordList>
        <value></value>
    </keywordList>
    <layername>{layer_name}</layername>
    <srs>
        <spatialrefsys>
            {qgis_template_spatialrefsys}
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
              {qgis_template_spatialrefsys}
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
