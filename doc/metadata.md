# Metadata

Layman is able to publish partial metadata records to [OGC Catalogue Service](https://www.opengeospatial.org/standards/cat) [Micka](http://micka.bnhelp.cz/). Records are partial because Layman does not know all metadata properties. Below are listed
- [metadata properties that are known to Layman](#metadata-properties-known-to-layman) 
- [metadata properties unknown to Layman](#metadata-properties-unknown-to-layman), that Layman is aware of. 

Although metadata records sent to Micka are partial, they can (and should) be completed using Micka web editor GUI. URL of layer's metadata record leading to Micka's GUI is available in [GET Workspace Layer](rest.md#get-workspace-layer) response as `metadata.record_url` property. To complete metadata records, just open this URL in browser, log in to micka as editor or admin, and complete the record.

On POST requests, Layman automatically creates metadata record using CSW with values of all known properties. On PATCH requests, Layman also automatically updates metadata record, but only for subset of synchronizable metadata properties, whose values were `equal` in Metadata Comparison response at the time just when PATCH started.

Properties listed below contains
- unique name (as heading)
- multiplicity of the property (usually 1 or 1..*)
- shape (type) of the property value
- example of the property value
- if the property is synchronizable on PATCH request or not
- XPath expressions pointing to specific placement of the property inside metadata document 


## Metadata properties known to Layman

### abstract
Multiplicity: 1

Shape: String

Example: `"Klasifikace pokryvu zemského povrchu v rozsahu ČR."`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:abstract/gco:CharacterString/text()`

XPath for Map: `/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:abstract/gco:CharacterString/text()`


### extent
Multiplicity: 1

Shape: Array of four numbers `[min latitude, min longitude, max latitude, max longitude]`

Example: `[11.87, 48.12, 19.13, 51.59]`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement[gmd:EX_GeographicBoundingBox]/gmd:EX_GeographicBoundingBox/*/gco:Decimal/text()`

XPath for Map: `/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/srv:extent/gmd:EX_Extent/gmd:geographicElement[gmd:EX_GeographicBoundingBox]/gmd:EX_GeographicBoundingBox/*/gco:Decimal/text()`


### graphic_url
Multiplicity: 1

Shape: String

Example: `"http://layman_test_run_1:8000/rest/workspace1/layers/ne_110m_admin_0_countries_shp/thumbnail"`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview[gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString]/gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString/text()`

XPath for Map: `/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:graphicOverview[gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString]/gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString/text()`


### identifier
Multiplicity: 1

Shape: Object with keys and values:
- **identifier**: String. Identifier itself.
- **label**: String. Identifier label.

Example: 
```
{
    "identifier": "http://layman_test_run_1:8000/rest/testuser1/layers/ne_110m_admin_0_countries_shp",
    "label": "ne_110m_admin_0_countries_shp"
}
```

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:MD_Identifier/gmd:code/gmx:Anchor/@xlink:href`

XPath for Map: `/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:MD_Identifier/gmd:code/gmx:Anchor/@xlink:href`


### language
Guessed from text attributes. Always empty for raster layers.

Multiplicity: 1..n

Shape: Array of strings

Example: `["cze", "eng"]`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:language/gmd:LanguageCode/@codeListValue`


### layer_endpoint
Multiplicity: 1

Shape: String

Example: `"http://layman_test_run_1:8000/rest/workspace1/layers/ne_110m_admin_0_countries_shp"`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link"]/gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()`


### map_endpoint
Multiplicity: 1

Shape: String

Example: `"http://layman_test_run_1:8000/rest/workspace1/maps/svet"`

Synchronizable: yes

XPath for Map: `/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link" and gmd:CI_OnlineResource/gmd:function/gmd:CI_OnLineFunctionCode/@codeListValue="information"]/gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()`


### map_file_endpoint
Multiplicity: 1

Shape: String

Example: `"http://layman_test_run_1:8000/rest/workspace1/maps/svet/file"`

Synchronizable: yes

XPath for Map: `/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link" and gmd:CI_OnlineResource/gmd:function/gmd:CI_OnLineFunctionCode/@codeListValue="download"]/gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()`


### md_date_stamp
Multiplicity: 1

Shape: String

Example: `"2007-05-25"`

Synchronizable: no, but it's updated if at least one other property is being synced

XPath for Layer: `/gmd:MD_Metadata/gmd:dateStamp/gco:Date/text()`

XPath for Map: `/gmd:MD_Metadata/gmd:dateStamp/gco:Date/text()`


### md_file_identifier
Multiplicity: 1

Shape: String

Example: `"m-91147a27-1ff4-4242-ba6d-faffb92224c6"`

Synchronizable: no

XPath for Layer: `/gmd:MD_Metadata/gmd:fileIdentifier/gco:CharacterString/text()`

XPath for Map: `/gmd:MD_Metadata/gmd:fileIdentifier/gco:CharacterString/text()`


### md_language
Guessed from title and description.

Multiplicity: 1

Shape: String

Example: `"cze"`

Synchronizable: no

XPath for Layer: `/gmd:MD_Metadata/gmd:language/gmd:LanguageCode/@codeListValue`

XPath for Map: `/gmd:MD_Metadata/gmd:language/gmd:LanguageCode/@codeListValue`
 

### operates_on
Multiplicity: 1..*

Shape: Object with keys and values:
- **xlink:href**: String. Link to other metadata record.
- **xlink:title**: String. Reference title.

Example: 
```
{
    "xlink:title": "http://localhost:3080/csw?SERVICE=CSW&amp;VERSION=2.0.2&amp;REQUEST=GetRecordById&amp;OUTPUTSCHEMA=http://www.isotc211.org/2005/gmd&amp;ID=m-39cc8994-adbc-427a-8522-569eb7e691b2#_m-39cc8994-adbc-427a-8522-569eb7e691b2",
    "xlink:href": "hranice"
}
```

Synchronizable: yes

XPath for Map: `/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/srv:operatesOn[@xlink:href]/@xlink:href`


### publication_date
Multiplicity: 1

Shape: String

Example: `"2007-05-25"`

Synchronizable: no

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="publication"]]/gmd:CI_Date/gmd:date/gco:Date/text()`

XPath for Map: `/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="publication"]]/gmd:CI_Date/gmd:date/gco:Date/text()`


### reference_system
Multiplicity: 1..*

Shape: Array of integers (EPSG codes).

Example: `[3857, 4326]`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:referenceSystemInfo[gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor[starts-with(@xlink:href, "http://www.opengis.net/def/crs/EPSG/0/")]]/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor/@xlink:href`

XPath for Map: `/gmd:MD_Metadata/gmd:referenceSystemInfo[gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor[starts-with(@xlink:href, "http://www.opengis.net/def/crs/EPSG/0/")]]/gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor/@xlink:href`


### revision_date
Multiplicity: 1

Shape: String

Example: `"2007-05-25"`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="revision"]]/gmd:CI_Date/gmd:date/gco:Date/text()`

XPath for Map: `/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode[@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and @codeListValue="revision"]]/gmd:CI_Date/gmd:date/gco:Date/text()`


### spatial_resolution
Multiplicity: 1

Shape: Object with one of following keys:
- *scale_denominator*: Integer. Scale denominator, used for vector data, guessed from distances between vertices of line and polygon features.
- *ground_sample_distance*: Object. Ground sample distance, used for raster data, read from normalized raster.  
  Keys:
  - **value**: Float. Value of ground sample distance.
  - **uom**: String. Unit of measurement of ground sample distance.

Example: 
```json5
// Spatial resolution of vector data:
{
    "scale_denominator": 10000
}
```

```json5
// Spatial resolution of raster data:
{
    "ground_sample_distance": {
        "value": 123.45,
        "uom": "m"
    }
}
```

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution`


### temporal_extent
Multiplicity: 1..n

Shape: Array of strings

Example: `["2022-03-16T00:00:00.000Z", "2022-03-19T00:00:00.000Z"]`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:temporalElement[gmd:EX_TemporalExtent/gmd:extent/gml:TimeInstant/gml:timePosition]/gmd:EX_TemporalExtent/gmd:extent/gml:TimeInstant/gml:timePosition/text()`


### title
Multiplicity: 1

Shape: String

Example: `"World Countries"`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString/text()`

XPath for Map: `/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString/text()`


### wfs_url
It contains standard SERVICE, REQUEST, and VERSION parameters and non-standard LAYERS parameter that holds name of the feature type at given WFS instance. It is filled for vector layers, not raster ones.

Multiplicity: 1

Shape: String

Example: `"http://localhost:8600/geoserver/workspace1/ows?SERVICE=WFS&REQUEST=GetCapabilities&VERSION=2.0.0&LAYERS=layer"`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WFS-2.0.0-http-get-capabilities"]/gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()`


### wms_url
It contains standard SERVICE, REQUEST, and VERSION parameters and non-standard LAYERS parameter that holds name of the layer at given WMS instance.

Multiplicity: 1

Shape: String

Example: `"http://localhost:8600/geoserver/workspace1_wms/ows?SERVICE=WMS&REQUEST=GetCapabilities&VERSION=1.3.0&LAYERS=layer"`

Synchronizable: yes

XPath for Layer: `/gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine[gmd:CI_OnlineResource/gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WMS-1.3.0-http-get-capabilities"]/gmd:CI_OnlineResource/gmd:linkage/gmd:URL/text()`


## Metadata properties unknown to Layman

### md_organisation_name
Multiplicity: 1

Shape: String

Example: `"Ministerstvo životního prostředí ČR"`

Synchronizable: no

XPath for Layer: `/gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString/text()`

XPath for Map: `/gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString/text()`


### organisation_name
Multiplicity: 1

Shape: String

Example: `"Ministerstvo životního prostředí ČR"`

Synchronizable: no

XPath for Layer: `/gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString/text()`

XPath for Map: `/gmd:MD_Metadata/gmd:identificationInfo/srv:SV_ServiceIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString/text()`

