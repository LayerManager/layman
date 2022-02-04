<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld"
                           xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc"
                           version="1.0.0">
    <sld:NamedLayer>
        <sld:Name>Default Styler</sld:Name>
        <sld:UserStyle>
            <sld:Name>Default Styler</sld:Name>
            <sld:Title>Generic</sld:Title>
            <sld:Abstract>Generic style</sld:Abstract>
            <sld:FeatureTypeStyle>
                <sld:Name>name</sld:Name>
                <sld:Rule>
                    <sld:Name>raster</sld:Name>
                    <sld:Title>raster</sld:Title>
                    <ogc:Filter>
                        <ogc:PropertyIsEqualTo>
                            <ogc:Function name="isCoverage"/>
                            <ogc:Literal>true</ogc:Literal>
                        </ogc:PropertyIsEqualTo>
                    </ogc:Filter>
                    <sld:RasterSymbolizer>
                        <sld:ColorMap>
                            <sld:ColorMapEntry color="#0000ff" quantity="0.1"/>
                            <sld:ColorMapEntry color="#009933" quantity="0.3"/>
                            <sld:ColorMapEntry color="#ff9900" quantity="0.6"/>
                            <sld:ColorMapEntry color="#ff0000" quantity="0.9"/>
                            <sld:ColorMapEntry color="#ff0000" quantity="0.99"/>
                            <sld:ColorMapEntry color="#ff0000" opacity="0" quantity="1.0"/>
                        </sld:ColorMap>
                    </sld:RasterSymbolizer>
                </sld:Rule>
            </sld:FeatureTypeStyle>
        </sld:UserStyle>
    </sld:NamedLayer>
</sld:StyledLayerDescriptor>
