<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  
  <!-- Identity transformation to copy everything by default -->
  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>
  
  <!-- Match and copy the root elements (mxfile, diagram, mxGraphModel) -->
  <xsl:template match="mxfile">
    <xsl:copy>
      <xsl:apply-templates select="@*|diagram" />
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="diagram">
    <xsl:copy>
      <xsl:apply-templates select="@*|mxGraphModel" />
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="mxGraphModel">
    <xsl:copy>
      <xsl:apply-templates select="@*|root" />
    </xsl:copy>
  </xsl:template>
  
  <!-- Match and transform i* elements to PIM elements -->
  
  <!-- Template to check if the object belongs to an actor/role/agent that is a CPC -->
  <xsl:template name="check-cpc-ownership">
    <!-- Accept the object ID to check -->
    <xsl:param name="objectId" />
    
    <!-- Get the parent boundary ID -->
    <xsl:variable name="boundaryId" select="../object[@id=$objectId]/mxCell/@parent" />
    
    <!-- Get the 'owns' relationship where the boundary is the target -->
    <xsl:variable name="ownsId" select="../object[@type='owns' and mxCell/@target=$boundaryId]/@id" />
    
    <!-- Get the actor/role/agent that owns the boundary (source of 'owns' relationship) -->
    <xsl:variable name="actorId" select="../object[@id=../object[@type='owns' and @id=$ownsId]/mxCell/@source]/@id" />
    
    <!-- Check if the actor/role/agent has is_a_cpc='true' -->
    <xsl:variable name="isCPC" select="../object[@id=$actorId and (@type='actor' or @type='agent' or @type='role') and @is_a_cpc='true']" />
    
    <!-- Output true if it matches, otherwise false -->
    <xsl:choose>
      <xsl:when test="$isCPC">
        <xsl:value-of select="'true'" />
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="'false'" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <!-- Generic array calculation for contributions or qualifications -->
  <xsl:template name="calculate_array">
    <xsl:param name="id" />
    <xsl:param name="type" />
    
    <!-- Process contributions or qualifications linked to the object -->
    <xsl:for-each select="//object[@type=$type and (mxCell/@source = $id or mxCell/@target = $id)]">
      <xsl:variable name="relatedObjectId" select="if (mxCell/@source = $id) then mxCell/@target else mxCell/@source" />
      <xsl:variable name="relatedObjectLabel" select="//object[@id = $relatedObjectId]/@label" />
      <xsl:variable name="relationshipValue" select="@value" />
      <xsl:variable name="relatedObjectType" select="//object[@id = $relatedObjectId]/@type" />
      
      <!-- Determine if the related object is a softgoal or another type -->
      <xsl:variable name="isSoftgoal" select="$relatedObjectType = 'softgoal'" />
      
      <!-- Build JSON-like structure for the array -->
      <xsl:if test="position() > 1">,</xsl:if>
      <xsl:text>{</xsl:text>
      
      <!-- Use "softgoal_id" for softgoals, otherwise "object_id" -->
      <xsl:if test="$isSoftgoal">
        <xsl:text> "softgoal_id": "</xsl:text>
      </xsl:if>
      <xsl:if test="not($isSoftgoal)">
        <xsl:text> "object_id": "</xsl:text>
      </xsl:if>
      <xsl:value-of select="$relatedObjectId" />
      <xsl:text>",</xsl:text>
      
      <!-- Include the label (name) of the related object -->
      <xsl:text> "name": "</xsl:text>
      <xsl:value-of select="$relatedObjectLabel" />
      
      <!-- If it's a contribution, include the contribution value -->
      <xsl:if test="$type = 'contribution'">
        <xsl:text>",</xsl:text>
        <xsl:text> "contribution": "</xsl:text>
        <xsl:value-of select="$relationshipValue" />
      </xsl:if>
      
      <xsl:text>"}</xsl:text>
    </xsl:for-each>
  </xsl:template>
  
  <!-- Template to create an mxGeometry structure between two objects -->
  <xsl:template name="create_geometry_midpoint">
    <xsl:param name="sourceId" />
    <xsl:param name="targetId" />
    <xsl:param name="operatorWidth" />
    <xsl:param name="operatorHeight" />
    
    <!-- Capture the geometry of the source element -->
    <xsl:variable name="sourceX" select="//object[@id=$sourceId]/mxCell/mxGeometry/@x" />
    <xsl:variable name="sourceY" select="//object[@id=$sourceId]/mxCell/mxGeometry/@y" />
    
    <xsl:variable name="sourceWidth" select="//object[@id=$sourceId]/mxCell/mxGeometry/@width" />
    <xsl:variable name="sourceHeight" select="//object[@id=$sourceId]/mxCell/mxGeometry/@height" />
    
    <xsl:variable name="sourceCenterX" select="$sourceX + ($sourceWidth div 2)" />
    <xsl:variable name="sourceCenterY" select="$sourceY + ($sourceHeight div 2)" />
    
    <!-- Capture the geometry of the target element -->
    <xsl:variable name="targetX" select="//object[@id=$targetId]/mxCell/mxGeometry/@x" />
    <xsl:variable name="targetY" select="//object[@id=$targetId]/mxCell/mxGeometry/@y" />
    
    <xsl:variable name="targetWidth" select="//object[@id=$targetId]/mxCell/mxGeometry/@width" />
    <xsl:variable name="targetHeight" select="//object[@id=$targetId]/mxCell/mxGeometry/@height" />
    
    <xsl:variable name="targetCenterX" select="$targetX + ($targetWidth div 2)" />
    <xsl:variable name="targetCenterY" select="$targetY + ($targetHeight div 2)" />
    
    <!-- Calculate the midpoint between the source and target elements -->
    <xsl:variable name="midX" select="($sourceCenterX + $targetCenterX) div 2 - $operatorWidth div 2" />
    <xsl:variable name="midY" select="($sourceCenterY + $targetCenterY) div 2 - $operatorHeight div 2" />
    
    <!-- Create the mxGeometry element -->
    <mxGeometry x="{$midX}" y="{$midY}" width="{$operatorWidth}" height="{$operatorHeight}" as="geometry" />
  </xsl:template>
  
  <!-- Template to create an mxGeometry structure of the closest edge of a rectangle to a mobiel object -->
  <xsl:template name="create_geometry_closestRectangleEdge">
    <xsl:param name="objectId" />
    <xsl:param name="objectWidth" />
    <xsl:param name="objectHeight" />
    <xsl:param name="rectangleId" />
    <xsl:param name="scale" />
    
    <!-- Capture and determine geometry of the mobile object -->
    <xsl:variable name="objectX" select="//object[@id=$objectId]/mxCell/mxGeometry/@x" />
    <xsl:variable name="objectY" select="//object[@id=$objectId]/mxCell/mxGeometry/@y" />
    <xsl:variable name="objectCenterX" select="$objectX + ($objectWidth div 2)" />
    <xsl:variable name="objectCenterY" select="$objectY + ($objectHeight div 2)" />
    
    <!-- Capture ande determine geometry of the rectangle -->
    <xsl:variable name="rectangleX" select="//object[@id=$rectangleId]/mxCell/mxGeometry/@x" />
    <xsl:variable name="rectangleY" select="//object[@id=$rectangleId]/mxCell/mxGeometry/@y" />
    <xsl:variable name="rectangleBaseWidth" select="//object[@id=$rectangleId]/mxCell/mxGeometry/@width" />
    <xsl:variable name="rectangleBaseHeight" select="//object[@id=$rectangleId]/mxCell/mxGeometry/@height" />
    <xsl:variable name="rectangleCenterX" select="$rectangleX + $rectangleBaseWidth div 2" />
    <xsl:variable name="rectangleCenterY" select="$rectangleY + $rectangleBaseHeight div 2" />
    <xsl:variable name="rectangleWidth" select="$rectangleBaseWidth * $scale" />
    <xsl:variable name="rectangleHeight" select="$rectangleBaseHeight * $scale" />
    
    <!-- Determine geometry of the edges of the rectangle -->
    <xsl:variable name="leftEdge" select="$rectangleCenterX - ($rectangleWidth div 2)" />
    <xsl:variable name="topEdge" select="$rectangleCenterY - ($rectangleHeight div 2)" />
    <xsl:variable name="rightEdge" select="$rectangleCenterX + ($rectangleWidth div 2)" />
    <xsl:variable name="bottomEdge" select="$rectangleCenterY + ($rectangleHeight div 2)" />
    
    <!-- Calculate closest X edge -->
    <xsl:variable name="closestEdgeX">
      <xsl:choose>
        <xsl:when test="$objectCenterX &lt; $leftEdge">
          <xsl:value-of select="$leftEdge" />
        </xsl:when>
        <xsl:when test="$objectCenterX &gt; $rightEdge">
          <xsl:value-of select="$rightEdge" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$objectX" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    
    <!-- Calculate closest Y edge -->
    <xsl:variable name="closestEdgeY">
      <xsl:choose>
        <xsl:when test="$objectCenterY &lt; $topEdge">
          <xsl:value-of select="$topEdge" />
        </xsl:when>
        <xsl:when test="$objectCenterY &gt; $bottomEdge">
          <xsl:value-of select="$bottomEdge" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$objectY" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    
    <!-- Coordinates adjusted in the context of the parent/(rectangle) -->
    <xsl:variable name="endX" select="$closestEdgeX - $rectangleX" />
    <xsl:variable name="endY" select="$closestEdgeY - $rectangleY" />
    
    <!-- Create the mxGeometry element -->
    <mxGeometry x="{$endX}" y="{$endY}" width="{$objectWidth}" height="{$objectHeight}" as="geometry" />
    
  </xsl:template>
  
  <!-- Combine Actor/Role/Agent with their owns relationship and Boundary -->
  <xsl:template match="object[(@type='actor' or @type='agent' or @type='role') and @is_a_cpc='true']">
    <xsl:variable name="agentId" select="@id" />
    
    <!-- Exclude unnecessary 'agent' elements with 'group' style -->
    <xsl:if test="not(./mxCell[@style='group;allowArrows=0;'])">
      
      <!-- Extract the 'owns' relationship element -->
      <xsl:variable name="owns" select="../object[@type='owns' and mxCell/@source=$agentId]" />
      
      <!-- Extract the target boundary ID from the owns relationship -->
      <xsl:variable name="boundaryId" select="$owns/mxCell/@target" />
      
      <!-- Extract the boundary element based on the boundaryId -->
      <xsl:variable name="boundary" select="../object[@id=$boundaryId]" />
      
      <!-- Extract the parent of the boundary element -->
      <xsl:variable name="boundaryParent" select="../object[@id=$boundary/mxCell/@parent]" />
      
      <object label="{@label}" type="cps_component" id_cim_parent="{$agentId}" id="{$boundaryId}" name="{@label}" description="{@description}">
        <mxCell style="swimlane;whiteSpace=wrap;html=1;" vertex="1" parent="1">
          <mxGeometry 
            x="{$boundaryParent/mxCell/mxGeometry/@x}"
            y="{$boundaryParent/mxCell/mxGeometry/@y}"  
            width="{$boundaryParent/mxCell/mxGeometry/@width}" 
            height="{$boundaryParent/mxCell/mxGeometry/@height}" 
            as="geometry">
            <!-- Include the mxRectangle -->
            <mxRectangle x="44" width="49.05" height="44" as="alternateBounds"/>
          </mxGeometry>
        </mxCell>
        
        <!-- Apply templates to the 'owns' element to retain its structure -->
        <xsl:apply-templates select="$owns" />
      </object>
      
    </xsl:if>
  </xsl:template>
  
  <!-- Goal to Operational Goal -->
  <xsl:template match="object[@type='goal' and not(mxCell/@parent='1')]">
    <xsl:variable name="goalId" select="@id" />
    
    <!-- Call the check-cpc-ownership template to verify if the goal belongs to a CPC -->
    <xsl:variable name="isCPC">
      <xsl:call-template name="check-cpc-ownership">
        <xsl:with-param name="objectId" select="$goalId" />
      </xsl:call-template>
    </xsl:variable>
    <xsl:if test="$isCPC='true'">
      
      <!-- Contribution Array -->
      <xsl:variable name="contributions">
        <xsl:call-template name="calculate_array">
          <xsl:with-param name="id" select="$goalId" />
          <xsl:with-param name="type" select="'contribution'" />
        </xsl:call-template>
      </xsl:variable>
      
      <!-- Qualification Array -->
      <xsl:variable name="qualifications">
        <xsl:call-template name="calculate_array">
          <xsl:with-param name="id" select="$goalId" />
          <xsl:with-param name="type" select="'qualification-link'" />
        </xsl:call-template>
      </xsl:variable>
      
      <!-- Declare variables for height and width -->
      <xsl:variable name="height" select="mxCell/mxGeometry/@height" />
      <xsl:variable name="width" select="mxCell/mxGeometry/@width" />

      <!-- Calculate the larger value between height and width -->
      <xsl:variable name="radius">
        <xsl:choose>
          <xsl:when test="$height &gt; $width">
            <xsl:value-of select="$height" />
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="$width" />
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <!-- Output the transformed object -->
      <object label="{@label}"
              type="operational_goal" 
              id_cim_parent="{@id}" 
              id="{@id}" 
              name="{@label}" 
              qualification_array="[{$qualifications}]" 
              contribution_array="[{$contributions}]"
              operation_modes_enabled = "{@operation_modes_enabled}"
              operation_modes_description = "{@operation_modes_description}"
              interval_in_milliseconds="{@interval_in_milliseconds}">
        <mxCell style="ellipse;whiteSpace=wrap;html=1;aspect=fixed;" vertex="1" parent="{mxCell/@parent}">
        <!-- Use the largest value as both height and width to make it a circle -->
        <mxGeometry x="{mxCell/mxGeometry/@x}" y="{mxCell/mxGeometry/@y}" width="{$radius}" height="{$radius}" as="geometry" />
        </mxCell>
      </object>
    </xsl:if>
  </xsl:template>
  
  <!-- Task to Action -->
  <xsl:template match="object[@type='task' and not(mxCell/@parent='1')]">
    <xsl:variable name="taskId" select="@id" />
    
    <xsl:variable name="isCPC">
      <xsl:call-template name="check-cpc-ownership">
        <xsl:with-param name="objectId" select="$taskId" />
      </xsl:call-template>
    </xsl:variable>
    <xsl:if test="$isCPC='true'">
      
      <!-- Contribution Array -->
      <xsl:variable name="contributions">
        <xsl:call-template name="calculate_array">
          <xsl:with-param name="id" select="$taskId" />
          <xsl:with-param name="type" select="'contribution'" />
        </xsl:call-template>
      </xsl:variable>
      
      <!-- Qualification Array -->
      <xsl:variable name="qualifications">
        <xsl:call-template name="calculate_array">
          <xsl:with-param name="id" select="$taskId" />
          <xsl:with-param name="type" select="'qualification-link'" />
        </xsl:call-template>
      </xsl:variable>
      
      <!-- Output the transformed object -->
      <object label="{@label}" type="action" id_cim_parent="{@id}" id="{@id}" name="{@label}" 
              input_parameters="{if (@input_parameters) then @input_parameters else ''}" 
              output_parameters="{if (@output_parameters) then @output_parameters else ''}" 
              qualification_array="[{$qualifications}]" contribution_array="[{$contributions}]"
              operation_modes_enabled="{@operation_modes_enabled}"
              operation_modes_description="{@operation_modes_description}">
        <mxCell style="rounded=0;whiteSpace=wrap;html=1;" vertex="1" parent="{mxCell/@parent}">
          <xsl:copy-of select="mxCell/mxGeometry" />
        </mxCell>
      </object>
    </xsl:if>
  </xsl:template>
  
  <!-- Resource to HW Resource or SW Resource -->
  <!-- Note: The "resource_type attribute is not present in the i* scratchpad by default; therefore this will have to be added in a previous process involving user interaction" -->
  <xsl:template match="object[@type='resource' and not(mxCell/@parent='1')]">
    <!-- Determine the resource type -->
    <xsl:variable name="resourceType" select="@resource_type" />
    
    <xsl:variable name="isCPC">
      <xsl:call-template name="check-cpc-ownership">
        <xsl:with-param name="objectId" select="@id" />
      </xsl:call-template>
    </xsl:variable>
    <xsl:if test="$isCPC='true'">
      <!-- Determine if the resource is hardware or software -->
      
      <!-- Contribution Array -->
      <xsl:variable name="contributions">
        <xsl:call-template name="calculate_array">
          <xsl:with-param name="id" select="@id" />
          <xsl:with-param name="type" select="'contribution'" />
        </xsl:call-template>
      </xsl:variable>
      
      <!-- Qualification Array -->
      <xsl:variable name="qualifications">
        <xsl:call-template name="calculate_array">
          <xsl:with-param name="id" select="@id" />
          <xsl:with-param name="type" select="'qualification-link'" />
        </xsl:call-template>
      </xsl:variable>
      
      <xsl:choose>
        <!-- If the resource type is 'hardware', create a hardware resource -->
        <xsl:when test="$resourceType = 'hardware'">
          <object label="{@label}" type="hw_resource" id_cim_parent="{@id}" id="{@id}" name="{@label}" qualification_array="[{$qualifications}]" contribution_array="[{$contributions}]">
            <mxCell style="verticalAlign=middle;align=center;shape=cube;spacingTop=8;spacingLeft=2;spacingRight=12;size=10;direction=south;fontStyle=0;html=1;whiteSpace=wrap;" vertex="1" parent="{mxCell/@parent}">
              <xsl:copy-of select="mxCell/mxGeometry" />
            </mxCell>
          </object>
        </xsl:when>
        
        <!-- Otherwise, create a software resource (default or when resource_type is 'software') -->
        <xsl:otherwise>
          <object label="{@label}" type="sw_resource" id_cim_parent="{@id}" id="{@id}" name="{@label}" qualification_array="[{$qualifications}]" contribution_array="[{$contributions}]" data_structure="{@data_structure}">
            <mxCell style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;" vertex="1" parent="{mxCell/@parent}">
              <xsl:copy-of select="mxCell/mxGeometry" />
            </mxCell>
          </object>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:template>
  
  
  <!-- Relationship elements 'needed-by' -->
  <xsl:template match="object[@type='needed-by']">
    <xsl:variable name="isCPC">
      <xsl:call-template name="check-cpc-ownership">
        <xsl:with-param name="objectId" select="@id" />
      </xsl:call-template>
    </xsl:variable>
    <xsl:if test="$isCPC='true'">
      <object label="" id_cim_parent="{@id}" type="relation_from_to" id="{@id}">
        <mxCell style="endArrow=classic;html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;
" edge="1" parent="{mxCell/@parent}" source="{mxCell/@source}" target="{mxCell/@target}">
          <xsl:copy-of select="mxCell/mxGeometry" />
        </mxCell>
      </object>
    </xsl:if>
  </xsl:template>
  
  <!-- Template for 'refinement' relationships -->
  <xsl:template match="object[@type='refinement']">
    
    <xsl:variable name="isCPC">
      <xsl:call-template name="check-cpc-ownership">
        <xsl:with-param name="objectId" select="@id" />
      </xsl:call-template>
    </xsl:variable>
    <xsl:if test="$isCPC='true'">
      
      <!-- Get the refinement type and convert it to uppercase -->
      <xsl:variable name="value" select="upper-case(@value)" />
      
      <!-- Determine the operator type and shape -->
      <xsl:variable name="operatorType" select="if ($value = 'AND') then 'and_ref_operator' else 'or_ref_operator'" />
      <xsl:variable name="operatorWidth" select="60" />
      <xsl:variable name="operatorHeight" select="80" />
      <xsl:variable name="shape" select="if ($value = 'AND') then 'or' else 'xor'" />
      
      <!-- Capture the source and target IDs -->
      <xsl:variable name="sourceId" select="mxCell/@source" />
      <xsl:variable name="targetId" select="mxCell/@target" />
      
      <!-- Generate simplified IDs using the target ID -->
      <xsl:variable name="operatorId" select="concat($targetId, '-operator-', $operatorType)" />
      <xsl:variable name="targetRelationId" select="concat($targetId, '-targetRelationship', $operatorType)" />
      
      <!-- First from-to relationship (source to operator) -->
      <object label="" id_cim_parent="{@id}" type="relation_from_to" id="{@id}">
        <mxCell style="endArrow=classic;html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;
" edge="1" parent="{mxCell/@parent}" source="{mxCell/@source}" target="{$operatorId}">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="0" y="0" as="sourcePoint" />
            <mxPoint x="0" y="0" as="targetPoint" />
          </mxGeometry>
        </mxCell>
      </object>
      
      <!-- Operator object (positioned at the midpoint) -->
      <object label="{$value}" name="" id_cim_parent="{@id}" type="{$operatorType}" id="{$operatorId}">
        <mxCell style="shape={$shape};whiteSpace=wrap;html=1;" vertex="1" parent="{mxCell/@parent}">
          
          <!-- Call the template to generate the mxGeometry -->
          <xsl:call-template name="create_geometry_midpoint">
            <xsl:with-param name="sourceId" select="$sourceId" />
            <xsl:with-param name="targetId" select="$targetId" />
            <xsl:with-param name="operatorWidth" select="$operatorWidth" />
            <xsl:with-param name="operatorHeight" select="$operatorHeight" />
          </xsl:call-template>
          
        </mxCell>
      </object>
      
      
      <!-- Second from-to relationship (operator to original target) -->
      <object label="" id_cim_parent="{@id}" type="relation_from_to" id="{$targetRelationId}">
        <mxCell style="endArrow=classic;html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;
" edge="1" parent="{mxCell/@parent}" source="{$operatorId}" target="{mxCell/@target}">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="0" y="0" as="sourcePoint" />
            <mxPoint x="0" y="0" as="targetPoint" />
          </mxGeometry>
        </mxCell>
      </object>
    </xsl:if>
  </xsl:template>
  
  <!-- Match any object of type resource, softgoal, goal, or task -->
  <xsl:template match="object[@type=('resource', 'softgoal', 'goal', 'task') and (mxCell/@parent='1')]">
    
    <xsl:variable name="dependeeId" select="//object[@type='dependency-link' and (mxCell/@source = current()/@id)]/mxCell/@target"/>
    <xsl:variable name="dependerId" select="//object[@type='dependency-link' and (mxCell/@target = current()/@id)]/mxCell/@source"/>
    <xsl:variable name="isDependerCPC">
      <xsl:call-template name="check-cpc-ownership">
        <xsl:with-param name="objectId" select="$dependerId" />
      </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="isDependeeCPC">
      <xsl:call-template name="check-cpc-ownership">
        <xsl:with-param name="objectId" select="$dependeeId" />
      </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="isCPC" select="if($isDependeeCPC='true' and $isDependerCPC='true') then 'true' else 'false'"/>
    
    <xsl:if test="$isCPC='true'">
      <!-- Determine the ids for every generated object -->
      <xsl:variable name="listenerThreadId" select="concat(@id, '-listener_thread')" />
      <xsl:variable name="commThreadId" select="concat(@id, '-comm_thread')" />
      <xsl:variable name="commRelationId" select="concat(@id, '-comm_relation')" />
      <xsl:variable name="mailSymbolId" select="concat(@id, '-mail_symbol')" />
      
      <!-- 
          Original label construction (commented out for consistency update):
          <xsl:variable name="listenerThreadLabel" select="concat(@label, ' - Listener Thread')" />
          <xsl:variable name="commThreadLabel" select="concat(@label, ' - Comm Thread')" />
          
          Updated to align with new terminology in the user interface.
          These labels will be shown in diagrams.net as node names for communication elements.
      -->
      <xsl:variable name="listenerThreadLabel" select="concat(@label, ' - message receiver')" />
      <xsl:variable name="commThreadLabel" select="concat(@label, ' - message sender')" />
      <!-- Consistency update section end -->
      
       
      <!-- Determine the required attributes for the dependee and depender -->   
      <xsl:variable name="dependeeType" select="//object[@id=$dependeeId]/@type"/>
      <xsl:variable name="dependeeLabel" select="//object[@id=$dependeeId]/@label"/>
      <xsl:variable name="dependeeQualifications">
        <xsl:call-template name="calculate_array">
          <xsl:with-param name="id" select="$dependeeId" />
          <xsl:with-param name="type" select="'qualification-link'" />
        </xsl:call-template>
      </xsl:variable>
      <xsl:variable name="dependeeContributions">
        <xsl:call-template name="calculate_array">
          <xsl:with-param name="id" select="$dependeeId" />
          <xsl:with-param name="type" select="'contribution'" />
        </xsl:call-template>
      </xsl:variable>
      
      
      <xsl:variable name="dependerType" select="//object[@id=$dependerId]/@type"/>
      <xsl:variable name="dependerLabel" select="//object[@id=$dependerId]/@label"/>
      <xsl:variable name="dependerQualifications">
        <xsl:call-template name="calculate_array">
          <xsl:with-param name="id" select="$dependerId" />
          <xsl:with-param name="type" select="'qualification-link'" />
        </xsl:call-template>
      </xsl:variable>
      <xsl:variable name="dependerContributions">
        <xsl:call-template name="calculate_array">
          <xsl:with-param name="id" select="$dependerId" />
          <xsl:with-param name="type" select="'contribution'" />
        </xsl:call-template>
      </xsl:variable>
      
      <!-- Determine the parent boundary's geometry for dependee -->
      <xsl:variable name="dependeeParent" select="//object[@id=$dependeeId]/mxCell/@parent"/>
      <xsl:variable name="dependeeBoundary" select="//object[@id=$dependeeParent]/mxCell/@parent"/>
      
      
      <!-- Determine the parent boundary's geometry for depender -->
      <xsl:variable name="dependerParent" select="//object[@id=$dependerId]/mxCell/@parent"/>
      <xsl:variable name="dependerBoundary" select="//object[@id=$dependerParent]/mxCell/@parent"/>
      
      <!-- Scale that alters how close are the listener thread and comm thread to the center of the Actor/Role/Agent when generated -->
      <xsl:variable name="scale" select="0.65"/>
      
      <!-- Listener Thread -->
      <object type="listener_thread"
              label="{$listenerThreadLabel}"  
              id="{$listenerThreadId}" 
              name ="{$listenerThreadLabel}" 
              id_cim_parent="{@id}"
              id_cim_type="{$dependerType}"
              cim_dependerElmnt_is_softgoal="{if($dependerType='softgoal') then 'true' else 'false'}"
              ifsg_softgoal_id="{if($dependerType='softgoal') then $dependerId else ''}"
              ifsg_softgoal_name="{if($dependerType='softgoal') then $dependerLabel else ''}"
              qualification_array="{if($dependerType='softgoal') then $dependerQualifications else ''}"
              contribution_array="{if($dependerType='softgoal') then $dependerContributions else ''}">
        
        <mxCell style="shape=trapezoid;perimeter=trapezoidPerimeter;whiteSpace=wrap;html=1;fixedSize=1;flipV=1;" 
                vertex="1" parent="{$dependerParent}">
          <xsl:call-template name="create_geometry_closestRectangleEdge">
            <xsl:with-param name="objectId" select="@id" />
            <xsl:with-param name="objectWidth" select="120" />
            <xsl:with-param name="objectHeight" select="60" />
            <xsl:with-param name="rectangleId" select="$dependerBoundary" />
            <xsl:with-param name="scale" select="$scale" />
          </xsl:call-template>
        </mxCell>
      </object>
      
      
      <!-- Comm Thread -->
      <object type="comm_thread" 
              label="{$commThreadLabel}"
              id="{$commThreadId}" 
              name="{$commThreadLabel}"
              id_cim_parent="{@id}"
              id_cim_type="{$dependeeType}"
              cim_dependeeElmnt_is_softgoal="{if($dependeeType='softgoal') then 'true' else 'false'}"
              ifsg_softgoal_id="{if($dependeeType='softgoal') then $dependeeId else ''}"
              ifsg_softgoal_name="{if($dependeeType='softgoal') then $dependeeLabel else ''}"
              qualification_array="{if($dependeeType='softgoal') then $dependeeQualifications else ''}"
              contribution_array="{if($dependeeType='softgoal') then $dependeeContributions else ''}"
              dependum_data_structure="{@dependum_data_structure}"
              interval_in_milliseconds="{@interval_in_milliseconds}"
              operation_modes_enabled="{@operation_modes_enabled}"
              operation_modes_description="{@operation_modes_description}">
        <mxCell style="shape=trapezoid;perimeter=trapezoidPerimeter;whiteSpace=wrap;html=1;fixedSize=1;flipH=0;flipV=0;" 
                vertex="1" parent="{$dependeeParent}">
          <xsl:call-template name="create_geometry_closestRectangleEdge">
            <xsl:with-param name="objectId" select="@id" />
            <xsl:with-param name="objectWidth" select="120" />
            <xsl:with-param name="objectHeight" select="60" />
            <xsl:with-param name="rectangleId" select="$dependeeBoundary" />
            <xsl:with-param name="scale" select="$scale" />
          </xsl:call-template>
        </mxCell>
      </object>
      
      <!-- Comm Relation -->
      <object label="" type="comm_relation" id="{$commRelationId}" id_cim_parent="{@id}">
        <mxCell style="endArrow=classic;html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;
" 
                edge="1" parent="1" source="{$commThreadId}" target="{$listenerThreadId}">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="230" y="580" as="sourcePoint" />
            <mxPoint x="210" y="400" as="targetPoint" />
          </mxGeometry>
        </mxCell>
      </object>
      
      <!-- Mail Symbol -->
      <object id="{$mailSymbolId}" type="mail_symbol" id_cim_parent="{@id}">
        <mxCell style="shape=message;html=1;outlineConnect=0;" vertex="1" 
                parent="{$commRelationId}">
          <mxGeometry width="20" height="14" relative="1" as="geometry">
            <mxPoint x="-10" y="-7" as="offset" />
          </mxGeometry>
        </mxCell>
      </object>
      
      <!-- Dependee Comm Relation -->
      <xsl:if test="$dependeeId and not($dependeeType='softgoal')">
        
        <xsl:variable name="commRelationDependeeId" select="concat(@id, '-comm_relation_dependee')" />
        <xsl:variable name="mailSymbolDependeeId" select="concat(@id, '-mail_symbol_dependee')" />
        
        <!-- Comm Relation -->
        <object label="" type="comm_relation" id="{$commRelationDependeeId}" id_cim_parent="{@id}">
          <mxCell style="endArrow=classic;html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;
" 
                  edge="1" parent="{//object[@id=$dependeeId]/mxCell/@parent}" source="{$dependeeId}" target="{$commThreadId}">
            <mxGeometry relative="1" as="geometry">
              <mxPoint x="230" y="580" as="sourcePoint" />
              <mxPoint x="210" y="400" as="targetPoint" />
            </mxGeometry>
          </mxCell>
        </object>
        
        <!-- Mail Symbol -->
        <object id="{$mailSymbolDependeeId}" type="mail_symbol" id_cim_parent="{@id}">
          <mxCell style="shape=message;html=1;outlineConnect=0;" vertex="1" 
                  parent="{$commRelationDependeeId}">
            <mxGeometry width="20" height="14" relative="1" as="geometry">
              <mxPoint x="-10" y="-7" as="offset" />
            </mxGeometry>
          </mxCell>
        </object>
        
      </xsl:if>
      
      <!-- Depender Comm Relation -->
      <xsl:if test="$dependerId and not($dependerType='softgoal')">
        
        <xsl:variable name="commRelationDependerId" select="concat(@id, '-comm_relation_depender')" />
        <xsl:variable name="mailSymbolDependerId" select="concat(@id, '-mail_symbol_depender')" />
        
        <!-- Comm Relation -->
        <object label="" type="comm_relation" id="{$commRelationDependerId}" id_cim_parent="{@id}">
          <mxCell style="endArrow=classic;html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;
" 
                  edge="1" parent="{//object[@id=$dependerId]/mxCell/@parent}" source="{$listenerThreadId}" target="{$dependerId}">
            <mxGeometry relative="1" as="geometry">
              <mxPoint x="230" y="580" as="sourcePoint" />
              <mxPoint x="210" y="400" as="targetPoint" />
            </mxGeometry>
          </mxCell>
        </object>
        
        <!-- Mail Symbol -->
        <object id="{$mailSymbolDependerId}" type="mail_symbol" id_cim_parent="{@id}">
          <mxCell style="shape=message;html=1;outlineConnect=0;" vertex="1" 
                  parent="{$commRelationDependerId}">
            <mxGeometry width="20" height="14" relative="1" as="geometry">
              <mxPoint x="-10" y="-7" as="offset" />
            </mxGeometry>
          </mxCell>
        </object>
        
      </xsl:if>
    </xsl:if>
  </xsl:template>
  
  
  <!-- Remove boundary elements (Container element of actors, agents and roles) -->
  <xsl:template match="object[@type='boundary']">
    <!-- Do nothing to remove the element -->
  </xsl:template>
  
  <!-- Remove owns elements (Connection element of actors, agents and roles) -->
  <xsl:template match="object[@type='owns']">
    <!-- Do nothing to remove the element -->
  </xsl:template>
  
  <!-- Remove softgoal elements -->
  <xsl:template match="object[@type='softgoal' and not(mxCell/@parent='1')]">
    <!-- Do nothing to remove the element -->
  </xsl:template>
  
  <!-- Remove contribution elements (Connection element of softgoals) -->
  <xsl:template match="object[@type='contribution']">
    <!-- Do nothing to remove the element -->
  </xsl:template>
  
  <!-- Remove qualification-link elements (Connection element of softgoals) -->
  <xsl:template match="object[@type='qualification-link']">
    <!-- Do nothing to remove the element -->
  </xsl:template>
  
  <!-- Remove dependency-link elements (Connection element for dependencies) -->
  <xsl:template match="object[@type='dependency-link']">
    <!-- Do nothing to remove the element -->
  </xsl:template>
  
  <!-- Remove objects with null type -->
  <xsl:template match="object[@type='']" />
  
  <xsl:template match="object[(@type='agent' or @type='role' or @type='actor') and @is_a_cpc='false']" />
  
  <!-- Remove mxCell remaining structures -->
  <xsl:template match="mxCell[@style='group;allowArrows=0;']" />
  
  <!-- Handle remaining elements or specific cases (if necessary) -->
  <xsl:template match="object">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()" />
    </xsl:copy>
  </xsl:template>
  
</xsl:stylesheet>

