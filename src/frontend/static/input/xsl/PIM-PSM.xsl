<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                exclude-result-prefixes="#all">
  
  <!-- Root transformation template -->
  <xsl:template match="/">
    <root id="{/mxfile/diagram/@id}" name="{/mxfile/diagram/@name}">
      <!-- Group by cps_component using its ID -->
      <xsl:for-each-group select="//object[@type='cps_component']" group-by="@id">
        <cpc id="{@id}" 
             name="{@name}" 
             description="{@description}" 
             id_cim_parent="{@id_cim_parent}">
          
          <!-- Extract all sw_resources related to this cps_component using mxCell/parent -->
          <xsl:for-each select="//object[@type='sw_resource'][mxCell/@parent = current-grouping-key()]">
            <sw_resource id="{@id}" 
                         name="{@name}" 
                         id_cim_parent="{@id_cim_parent}"
                         data_structure="{@data_structure_psm}"/>
          </xsl:for-each>
          
          <!-- Extract all hw_resources related to this cps_component using mxCell/parent -->
          <xsl:for-each select="//object[@type='hw_resource'][mxCell/@parent = current-grouping-key()]">
            <hw_resource id="{@id}" 
                         name="{@name}" 
                         id_cim_parent="{@id_cim_parent}"
                         integration_operation_description="{@integration_operation_description}"/>
          </xsl:for-each>
          
          <!-- Extract all actions related to this cps_component using mxCell/parent -->
          <xsl:for-each select="//object[@type='action'][mxCell/@parent = current-grouping-key()]">
            <function id="{@id}" 
                      name="{@name}"
                      id_cim_parent="{@id_cim_parent}" 
                      input_parameters="{@input_parameters_psm}" 
                      output_parameters="{@output_parameters_psm}" 
                      qualification_array="{@qualification_array}" 
                      contribution_array="{@contribution_array}"
                      operation_modes_enabled="{@operation_modes_enabled}"
                      operation_modes_description="{@operation_modes_description}"
                      operation_modes="{@operation_modes}">
            </function>
            
          </xsl:for-each>
          
          <!-- Extract all operational_goals related to this cps_component using mxCell/parent -->
          <xsl:for-each select="//object[@type='operational_goal'][mxCell/@parent = current-grouping-key()]">
            <thread id="{@id}" 
                    name="{@name}"
                    id_cim_parent="{@id_cim_parent}" 
                    qualification_array="{@qualification_array}" 
                    contribution_array="{@contribution_array}"
                    interval_in_milliseconds="{@interval_in_milliseconds}"
                    operation_modes_enabled="{@operation_modes_enabled}"
                    operation_modes_description="{@operation_modes_description}"
                    operation_modes="{@operation_modes}"/>
          </xsl:for-each>
          
          <!-- Extract all relation_from_to related to this cps_component using mxCell/parent -->
          <xsl:for-each select="//object[@type='relation_from_to'][mxCell/@parent = current-grouping-key()]">
            <xsl:variable name="sourceElement" select="mxCell/@source"/>
            <xsl:variable name="targetElement" select="mxCell/@target"/>
            
            <!-- Check if the target is connected to an 'and_ref_operator' -->
            <xsl:variable name="andRefOperatorTarget" 
              select="//object[@type='and_ref_operator'][@id = $targetElement]"/>
            <xsl:variable name="andRefOperatorSource" 
              select="//object[@type='and_ref_operator'][@id = $sourceElement]"/>
            
            <xsl:choose>
              <!-- If connected to an and_ref_operator (via target), handle the relation accordingly -->
              <xsl:when test="$andRefOperatorTarget">
                <xsl:variable name="operatorLabel" select="$andRefOperatorTarget/@label"/>
                
                <!-- If the target is connected to an and_ref_operator -->
                <xsl:if test="$andRefOperatorTarget and not($andRefOperatorSource)">
                  <xsl:variable name="targetRelation" 
                    select="//object[@type='relation_from_to'][mxCell/@source = $andRefOperatorTarget/@id]"/>
                  <relation id="{@id}" 
                            id_cim_parent="{@id_cim_parent}"
                            source="{$sourceElement}"
                            target="{$targetRelation/mxCell/@target}"
                            operator="{$operatorLabel}"/>
                </xsl:if>
                
              </xsl:when>
              
              <!-- Otherwise, handle the case as it was originally -->
              <xsl:when test="not($andRefOperatorTarget) and not($andRefOperatorSource)">
                <relation id="{@id}" 
                          id_cim_parent="{@id_cim_parent}"
                          target="{mxCell/@target}"
                          source="{mxCell/@source}"/>
              </xsl:when>
            </xsl:choose>
          </xsl:for-each>
          
          <!-- Corrected Code -->
          <xsl:for-each select="//object[@type='comm_thread'][mxCell/@parent = current-grouping-key()]">
            <xsl:variable name="commThreadId" select="@id"/>
            <xsl:variable name="commRelation" select="//object[@type='comm_relation'][mxCell/@source=$commThreadId]"/>
            <xsl:variable name="listenerThread" select="//object[@type='listener_thread'][@id=$commRelation/mxCell/@target]"/>
            <commThread id="{@id}"
                        name="{@name}"
                        id_cim_parent="{@id_cim_parent}"
                        id_cim_type="{@id_cim_type}"
                        cim_dependeeElmnt_is_softgoal="{@cim_dependeeElmnt_is_softgoal}"
                        ifsg_softgoal_id="{@ifsg_softgoal_id}"
                        ifsg_softgoal_name="{@ifsg_softgoal_name}"
                        qualification_array="{@qualification_array}"
                        contribution_array="{@contribution_array}"
                        data_structure="{@data_structure_psm}"
                        interval_in_milliseconds="{@interval_in_milliseconds}"
                        operation_modes_enabled="{@operation_modes_enabled}"
                        operation_modes_description="{@operation_modes_description}"
                        operation_modes="{@operation_modes}"
                        listener_threadId="{$listenerThread/@id}"/>
          </xsl:for-each>
          
          <xsl:for-each select="//object[@type='listener_thread'][mxCell/@parent = current-grouping-key()]">
            <!-- Corrected variable definitions -->
            <xsl:variable name="listenerId" select="@id"/>
            
            <xsl:variable name="commRelation" select="//object[@type='comm_relation'][mxCell/@target=$listenerId]"/>
            <xsl:variable name="commThread" select="//object[@type='comm_thread'][@id=$commRelation/mxCell/@source]"/>
            <xsl:variable name="commThreadParent" select="$commThread/mxCell/@parent"/>
            <xsl:variable name="commThreadParent" select="//object[@type='cps_component'][@id=$commThreadParent]"/>
            
            <listenerThread id="{@id}"
                            name="{@name}"
                            id_cim_parent="{@id_cim_parent}"
                            id_cim_type="{@id_cim_type}"
                            cim_dependerElmnt_is_softgoal="{@cim_dependerElmnt_is_softgoal}"
                            ifsg_softgoal_id="{@ifsg_softgoal_id}"
                            ifsg_softgoal_name="{@ifsg_softgoal_name}"
                            qualification_array="{@qualification_array}"
                            contribution_array="{@contribution_array}"
                            data_structure="{$commThread/@dependum_data_structure}"
                            interval_in_milliseconds="{$commThread/@interval_in_milliseconds}"
                            operation_modes_enabled="{$commThread/@operation_modes_enabled}"
                            operation_modes_description="{$commThread/@operation_modes_description}"
                            operation_modes="{$commThread/@operation_modes}"
                            comm_threadId="{$commThread/@id}"
                            comm_threadCPCId="{$commThreadParent/@id}"/>
          </xsl:for-each>
          
          <xsl:for-each select="//object[@type='comm_relation'][mxCell/@parent = current-grouping-key()]">
            <commRelation id="{@id}"
                          id_cim_parent="{@id_cim_parent}"
                          source="{mxCell/@source}"
                          target="{mxCell/@target}"/>
          </xsl:for-each>
          
          
        </cpc>
      </xsl:for-each-group>
    </root>
  </xsl:template>
</xsl:stylesheet>








