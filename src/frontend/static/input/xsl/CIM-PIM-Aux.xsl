<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:key name="objectsById" match="object" use="@id"/>

    <!-- This script is meant to be used after the  PIM_transform_script, so that the duplicate elements(those with the same id) can be removed in order to avoid errors when viewing the draw.io model-->

    <xsl:template match="/mxfile">
        <mxfile>
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates select="diagram"/>
        </mxfile>
    </xsl:template>

    <xsl:template match="diagram">
        <xsl:copy>
            <xsl:copy-of select="@*"/>
            <mxGraphModel>
                <xsl:copy-of select="mxGraphModel/@*"/>
                <root>
                    <!-- Copy the first two mxCell elements -->
                    <xsl:copy-of select="mxGraphModel/root/mxCell[@id='0' or @id='1']"/>

                    <!-- Copy unique object elements -->
                    <xsl:for-each select="mxGraphModel/root/object[generate-id() = generate-id(key('objectsById', @id)[1])]">
                        <xsl:copy-of select="."/>
                    </xsl:for-each>
                </root>
            </mxGraphModel>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>



