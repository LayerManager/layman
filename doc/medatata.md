# Metadata

Layman is able to publish partial metadata records to [OGC Catalogue Service](https://www.opengeospatial.org/standards/cat) [Micka](http://micka.bnhelp.cz/). Records are partial because Layman does not know all metadata properties. Below are listed
- [metadata properties that are known to Layman](#metadata-properties-known-to-layman) 
- [metadata properties guessable by Layman](#metadata-properties-guessable-by-layman) (not yet implemented) 
- [metadata properties unknown to Layman](#metadata-properties-unknown-to-layman), that are needed to create metadata record acceptable by Micka. 

Although metadata records sent to Micka are partial, they can (and should) be completed using Micka web editor GUI.

Properties listed below contains XPath expression pointing to specific placement of the property inside metadata document. All listed metadata properties on Micka can be synced with metadata properties provided by Layman, whereas only some properties on Layman can be synced with properties provided by Micka (only `title` and `abstract`). No synchronization is implemented yet.

## Metadata properties known to Layman

### file_identifier
XPath
- `gmd:MD_Metadata/gmd:fileIdentifier/gco:CharacterString/text()`
  - multiplicity 1
  
### reference_system
XPath
- `gmd:MD_Metadata/gmd:referenceSystemInfo`
  - multiplicity 1..n, one per reference system
  - `gmd:MD_ReferenceSystem/gmd:referenceSystemIdentifier/gmd:RS_Identifier/gmd:code/gmx:Anchor`
    - multiplicity 1
    - `@xlink:href`
      - link to http://www.opengis.net/def/crs/EPSG/0/...
    - `text()`
      - EPSG:code

### title
XPath
- `gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:title/gco:CharacterString/text()`
  - multiplicity 1

### date
XPath
- `gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode/@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="publication"]/gmd:CI_Date/gmd:date/gco:Date/text()`
  - multiplicity 1
  - publication date
- `gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:date[gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode/@codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode" and gmd:CI_Date/gmd:dateType/gmd:CI_DateTypeCode/@codeListValue="revision"]/gmd:CI_Date/gmd:date/gco:Date/text()`
  - multiplicity 1
  - revision date

Synchronizable from Micka to Layman: False

### data_identifier
XPath
- `gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:citation/gmd:CI_Citation/gmd:identifier/gmd:MD_Identifier/gmd:code/gmx:Anchor/@xlink:href`
    - multiplicity 1

### abstract
XPath
- `gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/(gmd:abstract/gco:CharacterString/text()|gmd:abstract/[@gco:nilReason="unknown"])`
  - multiplicity 1

### graphic_url
XPath
- `gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString/text()`
    - multiplicity 1

XPath
### extent
- `gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:extent/gmd:EX_Extent/gmd:geographicElement/gmd:EX_GeographicBoundingBox`
    - multiplicity 1
    - `gmd:westBoundLongitude/gco:Decimal/text()`
      - multiplicity 1
    - `gmd:eastBoundLongitude/gco:Decimal/text()`
      - multiplicity 1
    - `gmd:southBoundLatitude/gco:Decimal/text()`
      - multiplicity 1
    - `gmd:northBoundLatitude/gco:Decimal/text()`
      - multiplicity 1

### wms_url
XPath
- `gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource[gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WMS-1.3.0"]/gmd:linkage/gmd:URL/text()`
  - multiplicity 1

### wfs_url
XPath
- `gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource[gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/OGC:WFS-2.0.0"]/gmd:linkage/gmd:URL/text()`
  - multiplicity 1

### layer_endpoint
XPath
- `gmd:MD_Metadata/gmd:distributionInfo/gmd:MD_Distribution/gmd:transferOptions/gmd:MD_DigitalTransferOptions/gmd:onLine/gmd:CI_OnlineResource[gmd:protocol/gmx:Anchor/@xlink:href="https://services.cuzk.cz/registry/codelist/OnlineResourceProtocolValue/WWW:LINK-1.0-http--link"]/gmd:linkage/gmd:URL/text()`
  - multiplicity 1

## Metadata properties guessable by Layman

### scale_denominator
XPath
- `gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:spatialResolution/gmd:MD_Resolution/gmd:equivalentScale/gmd:MD_RepresentativeFraction/(gmd:denominator/gco:Integer/text()|gmd:denominator/[@gco:nilReason="unknown"])`
  - multiplicity 1

### dataset_language
XPath
- `gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/(gmd:language/gmd:LanguageCode[@codeList="http://www.loc.gov/standards/iso639-2/"]/@codeListValue|gmd:language/[@gco:nilReason="unknown"])`
  - multiplicity 1

## Metadata properties unknown to Layman

### organisation_name
XPath
- `gmd:MD_Metadata/gmd:contact/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString/text()`
  - multiplicity 1

### data_organisation_name
XPath
- `gmd:MD_Metadata/gmd:identificationInfo/gmd:MD_DataIdentification/gmd:pointOfContact/gmd:CI_ResponsibleParty/gmd:organisationName/gco:CharacterString/text()`
  - multiplicity 1

