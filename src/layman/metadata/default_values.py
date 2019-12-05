
_TODO = "TODO"

######################################################################################################################
# KNOWN TO LAYMAN
######################################################################################################################

# layer UUID with prefix "m"
file_identifier = 'mca238200-8200-1a23-9399-42c9fca53542'

# layer: "dataset"
# map composition: "application"
hierarchy_level = '<gmd:MD_ScopeCode codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#MD_ScopeCode" codeListValue="dataset">dataset</gmd:MD_ScopeCode>'

# EPSG
reference_system = '<gmx:Anchor xlink:href="http://www.opengis.net/def/crs/EPSG/0/4258">EPSG:4258</gmx:Anchor>'

# title of data
title = 'CORINE - Krajinný pokryv CLC 90'

# date of dataset
# check GeoServer's REST API, consider revision or publication dateType
date = f"""
<gmd:CI_Date>
    <gmd:date>
        <gco:Date>2007-05-25</gco:Date>
    </gmd:date>
    <gmd:dateType>
        <gmd:CI_DateTypeCode codeListValue="revision" codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_DateTypeCode">revision</gmd:CI_DateTypeCode>
    </gmd:dateType>
</gmd:CI_Date>
"""

# it must be URI, but text node is optional (MZP-CORINE)
# it can point to Layman's Layer endpoint
data_identifier = '<gmx:Anchor xlink:href="http://www.env.cz/data/corine/1990">MZP-CORINE</gmx:Anchor>'

abstract = 'Klasifikace pokryvu zemského povrchu v rozsahu ČR'

# point to Layer Thumbnail endpoint
graphic_url = 'http://www.geology.cz/img/ikony/ikonky66/wms/wms_CGS_G-VDC-POD-WMS.png'

# only for layers, otherwise empty string
spatial_representation = f"""
<gmd:spatialRepresentationType>
    <gmd:MD_SpatialRepresentationTypeCode codeListValue="vector" codeList="http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#MD_SpatialRepresentationTypeCode">vector</gmd:MD_SpatialRepresentationTypeCode>
</gmd:spatialRepresentationType>
"""

extent = f"""
<gmd:EX_GeographicBoundingBox>
    <gmd:westBoundLongitude>
        <gco:Decimal>11.87</gco:Decimal>
    </gmd:westBoundLongitude>
    <gmd:eastBoundLongitude>
        <gco:Decimal>19.13</gco:Decimal>
    </gmd:eastBoundLongitude>
    <gmd:southBoundLatitude>
        <gco:Decimal>48.12</gco:Decimal>
    </gmd:southBoundLatitude>
    <gmd:northBoundLatitude>
        <gco:Decimal>51.59</gco:Decimal>
    </gmd:northBoundLatitude>
</gmd:EX_GeographicBoundingBox>
"""

wms_url = "http://www.env.cz/corine/data/download.zip"

wfs_url = "http://www.env.cz/corine/data/download.zip"

layer_endpoint = "http://layman.lesprojekt.cz/rest/username/layers/layername"

######################################################################################################################
# GUESSABLE BY LAYMAN
######################################################################################################################

scale_denominator = '<gmd:denominator gco:nilReason="unknown" />'

"""
# scale_denominator = f"""
# <gmd:denominator>
#     <gco:Integer>100000</gco:Integer>
# </gmd:denominator>
# """

# code for no language is "zxx"
dataset_language = f"<gmd:LanguageCode codeListValue=\"{_TODO}\" codeList=\"http://www.loc.gov/standards/iso639-2/\">{_TODO}</gmd:LanguageCode>"

######################################################################################################################
# UNKNOWN TO LAYMAN
######################################################################################################################

# contact to get info about metadata record
contact = f"""
<gmd:CI_ResponsibleParty>
    <gmd:organisationName>
        <gco:CharacterString>{_TODO}</gco:CharacterString>
    </gmd:organisationName>
    <gmd:contactInfo>
        <gmd:CI_Contact>
            <gmd:address>
                <gmd:CI_Address>
                    <gmd:electronicMailAddress>
                        <gco:CharacterString>{_TODO}</gco:CharacterString>
                    </gmd:electronicMailAddress>
                </gmd:CI_Address>
            </gmd:address>
            <gmd:onlineResource>
                <gmd:CI_OnlineResource>
                    <gmd:linkage>
                        <gmd:URL>{_TODO}</gmd:URL>
                    </gmd:linkage>
                </gmd:CI_OnlineResource>
            </gmd:onlineResource>
        </gmd:CI_Contact>
    </gmd:contactInfo>
    <gmd:role>
        <gmd:CI_RoleCode codeListValue=\"pointOfContact\" codeList=\"http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_RoleCode\">pointOfContact</gmd:CI_RoleCode>
    </gmd:role>
</gmd:CI_ResponsibleParty>
"""

data_contact = f"""
<gmd:CI_ResponsibleParty>
    <gmd:organisationName>
        <gco:CharacterString>{_TODO}</gco:CharacterString>
    </gmd:organisationName>
    <gmd:contactInfo>
        <gmd:CI_Contact>
            <gmd:address>
                <gmd:CI_Address>
                    <gmd:electronicMailAddress>
                        <gco:CharacterString>{_TODO}</gco:CharacterString>
                    </gmd:electronicMailAddress>
                </gmd:CI_Address>
            </gmd:address>
            <gmd:onlineResource>
                <gmd:CI_OnlineResource>
                    <gmd:linkage>
                        <gmd:URL>{_TODO}</gmd:URL>
                    </gmd:linkage>
                </gmd:CI_OnlineResource>
            </gmd:onlineResource>
        </gmd:CI_Contact>
    </gmd:contactInfo>
    <gmd:role>
        <gmd:CI_RoleCode codeListValue=\"custodian\" codeList=\"http://standards.iso.org/iso/19139/resources/gmxCodelists.xml#CI_RoleCode\">custodian</gmd:CI_RoleCode>
    </gmd:role>
</gmd:CI_ResponsibleParty>
"""

inspire_theme_keyword = f"<gmx:Anchor xlink:href=\"{_TODO}\">{_TODO}</gmx:Anchor>"

topic_category = '<gmd:topicCategory gco:nilReason="unknown" />'
# topic_category = """
# <gmd:topicCategory>
#     <gmd:MD_TopicCategoryCode>environment</gmd:MD_TopicCategoryCode>
# </gmd:topicCategory>
# """

lineage = _TODO