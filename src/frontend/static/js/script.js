let xsltFiles = [];
let jsonFiles = [];

const debug = true;

// Paths to preset files
const PRESET_FILES = {
    "cim-pim": {
        xslt: [
            "/static/input/xsl/CIM-PIM.xsl",
            "/static/input/xsl/CIM-PIM-Aux.xsl"
        ],
        json: "/static/input/json/CIM-PIM-Rules.json"
    },
    "pim-psm": {
        xslt: [
            "/static/input/xsl/PIM-PSM.xsl"
        ],
        json: "/static/input/json/PIM-PSM-Rules.json"
    }
};

let currentPreset = "cim-pim"; // Default preset

// Function to read the uploaded XML file and display its content in the textarea
function handleXMLUpload(inputElement) {
    const file = inputElement.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            document.getElementById('inputXML').value = e.target.result;
        };
        reader.readAsText(file);
    }
}

// Generic function to handle file uploads for lists
function handleListedUpload(inputElement, fileList, updateListFunction) {
    const file = inputElement.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            // Check if the uploaded file is a JSON file
            if (file.name.endsWith('.json')) {
                // Clear the list if it's a JSON file
                fileList.length = 0; // Clear the existing list
            }
            // Add the new file to the list
            fileList.push({ name: file.name, content: e.target.result });
            updateListFunction(fileList);
        };
        reader.readAsText(file);
    }
}


// Generic function to update the displayed list of uploaded files
function updateFileList(fileList, listElementId) {
    const fileListElement = document.getElementById(listElementId);
    fileListElement.innerHTML = ''; // Clear the list first

    fileList.forEach((file, index) => {
        const li = document.createElement('li');
        li.textContent = file.name;

        if (currentPreset == "custom") {
            // Remove button for each file
            const removeButton = document.createElement('button');
            removeButton.textContent = "Remove";
            removeButton.onclick = () => removeListedFile(index, fileList, listElementId);
            li.appendChild(removeButton);
        }
        fileListElement.appendChild(li);
    });
}

// Generic function to remove a file from the list
function removeListedFile(index, fileList, listElementId) {
    fileList.splice(index, 1);
    updateFileList(fileList, listElementId); // Refresh the list
}

// Function to read and display XSLT files
function handleXSLTUpload(inputElement) {
    handleListedUpload(inputElement, xsltFiles, (list) => updateFileList(list, 'xslFileList'));
}

// Event listeners for file inputs
document.getElementById('xmlFileInput').addEventListener('change', function () {
    handleXMLUpload(this);
});

document.getElementById('xslFileInput').addEventListener('change', function () {
    handleXSLTUpload(this);
});

// Event listener for JSON upload
document.getElementById('jsonFileInput').addEventListener('change', function () {
    handleListedUpload(this, jsonFiles, (list) => updateFileList(list, 'jsonFileList'));
});

// Transformation process
document.getElementById('transformBtn').addEventListener('click', function () {
    const inputXML = document.getElementById('inputXML').value;

    // Function to recursively process each XSLT file in sequence
    function processTransformation(xml, xsltIndex) {
        if (xsltIndex >= xsltFiles.length) {
            // Check if the "pim-psm" mode is selected
            const isPimPsmSelected = document.getElementById('pimPSMPreset').checked;

            if (isPimPsmSelected) {
                // Get the selected values for platform and comm_tech
                const platform = document.getElementById('platforms').value;
                const commTech = document.getElementById('commTechs').value;

                // Parse the XML and add the new attributes to the <root> element
                const parser = new DOMParser();
                const xmlDoc = parser.parseFromString(xml, 'application/xml');
                const rootElement = xmlDoc.documentElement;

                // Add the 'platform' and 'comm_tech' attributes
                rootElement.setAttribute('platform', platform);
                rootElement.setAttribute('comm_tech', commTech);

                // Serialize the modified XML back to a string
                const serializer = new XMLSerializer();
                xml = serializer.serializeToString(xmlDoc);
            }

            // All transformations are done, display the final output
            document.getElementById('outputXML').value = xml;
            return;
        }

        const xsltFileContent = xsltFiles[xsltIndex].content;

        fetch('/transform', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                'inputXML': xml,
                'xslFile': xsltFileContent
            })
        })
            .then(response => response.json())
            .then(data => {
                // Pass the transformed result to the next XSLT transformation
                processTransformation(data.output, xsltIndex + 1);
            })
            .catch(error => console.error('Error:', error));
    }

    if (xsltFiles.length > 0) {
        // Start the transformation chain with the first XSLT file
        processTransformation(inputXML, 0);
    } else {
        alert('Please upload at least one XSLT file.');
    }
});

// Download output XML functionality
document.getElementById('downloadBtn').addEventListener('click', function () {
    const outputXML = document.getElementById('outputXML').value;
    const blob = new Blob([outputXML], { type: 'text/xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'output.xml';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
});

document.getElementById('applyRulesBtn').addEventListener('click', function () {
    let inputXML = document.getElementById('inputXML').value;

    if (jsonFiles.length > 0) {
        // Get the modification rules from the first JSON file
        const firstJsonFile = jsonFiles[0];

        try {
            const json = JSON.parse(firstJsonFile.content); // Parse the JSON content
            const modificationRules = json.modifications; // Get the modifications from the JSON

            // Populate the modal with questions
            populateQuestionnaireForm(modificationRules);
            openModal(); // Show the modal to the user

        } catch (error) {
            alert("Invalid JSON format in the first file.");
            console.error("JSON parse error:", error);
        }
    } else {
        alert('No JSON files uploaded. Please upload a valid JSON file with rules.');
    }
});

// Function to open the modal
function openModal() {
    document.getElementById('questionnaireModal').style.display = "block";
}

// Function to close the modal
function closeModal() {
    document.getElementById('questionnaireModal').style.display = "none";
}

// Function to apply the modifications to the XML
function applyModifications(inputXML, modificationRules, formData) {
    if (!modificationRules || modificationRules.length === 0) {
        console.log('No modifications found. Please upload a valid JSON with rules.');
        return inputXML; // Return unmodified XML if no rules are provided
    }

    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(inputXML, "text/xml");

    modificationRules.forEach((rule, modIndex) => {
        const xpathResult = evaluateXPath(xmlDoc, rule.xpath);

        xpathResult.forEach((node, elemIndex) => {
            rule.attributes.forEach(attribute => {
                const baseFieldName = `modification_${modIndex}_element_${elemIndex}_${attribute.name}`;

                // Recursive function to handle nested attributes
                function applyNestedAttributes(attr, parentValue, baseName) {
                    if (parentValue && attr.additionalAttribute && attr.additionalAttribute.conditional) {
                        if (parentValue === attr.additionalAttribute.conditional) {
                            const nestedFieldName = `${baseName}_${attr.additionalAttribute.attribute.name}`;

                            const nestedValue = formData[nestedFieldName];

                            if (nestedValue) {
                                if (attr.additionalAttribute.attribute.parametersTable) {
                                    // Handle table-based nested attributes
                                    node.setAttribute(attr.additionalAttribute.attribute.name, JSON.stringify(nestedValue));
                                } else {
                                    node.setAttribute(attr.additionalAttribute.attribute.name, nestedValue);
                                }
                            }
                            // Recursively handle deeper nested attributes, if any
                            applyNestedAttributes(attr.additionalAttribute.attribute, nestedValue, nestedFieldName);
                        }
                    }
                }

                if (attribute.parametersTable) {
                    // Handle table-based attributes
                    const tableData = formData[baseFieldName];

                    if (tableData) {
                        node.setAttribute(attribute.name, JSON.stringify(tableData)); // Set JSON string as attribute value
                    }
                } else if (attribute.additionalAttribute && attribute.additionalAttribute.conditional) {
                    // Handle conditional attributes and nested ones
                    const mainValue = formData[baseFieldName];

                    if (mainValue) {
                        node.setAttribute(attribute.name, mainValue);
                        applyNestedAttributes(attribute, mainValue, baseFieldName);
                    }
                } else if (attribute.options || attribute.freeTextArea || attribute.number) {
                    // Handle standard fields
                    const userValue = formData[baseFieldName];

                    if (userValue) {
                        node.setAttribute(attribute.name, userValue);
                    }
                }
            });
        });
    });

    // Serialize the modified XML back to a string and return it
    const serializer = new XMLSerializer();
    return serializer.serializeToString(xmlDoc);
}

// Updated populateQuestionnaireForm to include each matched element in the questionnaire
function populateQuestionnaireForm(modifications) {
    const form = document.getElementById('questionnaireForm');
    form.innerHTML = ''; // Clear the form first
    form.classList.add('modal-form'); // Add modal class to the form

    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(document.getElementById('inputXML').value, 'text/xml');

    // Helper function to extract data from an XML node
    function getNodeAttribute(node, attribute) {
        return node.getAttribute(attribute) || '';
    }

    // Recursive function to process attributes
    function createAttributeInputs(attribute, modIndex, elemIndex, baseName, node) {
        const container = document.createElement('div'); // Container for this attribute's inputs
        container.classList.add('attribute-container');

        // Add the hint section if it exists
        if (attribute.hint) {
            const hintContainer = document.createElement('div');
            hintContainer.classList.add('modal-hint-container');

            const hintHeader = document.createElement('h4');
            hintHeader.textContent = attribute.hint.header;
            hintHeader.classList.add('modal-hint-header');
            hintContainer.appendChild(hintHeader);

            const hintTextarea = document.createElement('textarea');
            hintTextarea.readOnly = true;
            hintTextarea.classList.add('modal-textarea-uneditable');

            // Gather hint elements from the XML node
            const hintValues = attribute.hint.elements.map(elementName => getNodeAttribute(node, elementName));
            hintTextarea.value = hintValues.filter(Boolean).join('\n');
            hintContainer.appendChild(hintTextarea);

            container.appendChild(hintContainer);
        }

        const questionLabel = document.createElement('label');
        questionLabel.textContent = attribute.statement;
        questionLabel.classList.add('modal-question-label');

        let input;
        if (attribute.options) {
            // Dropdown for `options`
            input = document.createElement('select');
            input.classList.add('modal-select');
            attribute.options.forEach(option => {
                const optionElement = document.createElement('option');
                optionElement.value = option;
                optionElement.textContent = option;
                input.appendChild(optionElement);
            });
        } else if (attribute.parametersTable) {
            // Unique container for each parameters table
            const tableContainer = document.createElement('div');
            tableContainer.classList.add('modal-parameters-table-container');

            // Table with headers based on parametersTable.headers
            const table = document.createElement('table');
            table.classList.add('modal-parameters-table');
            table.id = `${baseName}_${attribute.name}`;

            // Header row
            const tableHeaders = document.createElement('tr');
            attribute.parametersTable.headers.forEach(header => {
                const th = document.createElement('th');
                th.classList.add('modal-parameters-table-header');
                th.textContent = capitalizeWord(header);
                tableHeaders.appendChild(th);
            });
            const removeHeader = document.createElement('th');
            removeHeader.classList.add('modal-parameters-table-header');
            tableHeaders.appendChild(removeHeader);
            table.appendChild(tableHeaders);

            // Pre-fill table rows if `derivate_from` exists
            const derivedData = attribute.derivate_from ? JSON.parse(getNodeAttribute(node, attribute.derivate_from)) || [] : [];
            derivedData.forEach(rowData => {
                const row = document.createElement('tr');
                attribute.parametersTable.headers.forEach((header, index) => {
                    const cell = document.createElement('td');
                    cell.classList.add('modal-parameters-table-cell');
                    const cellInput = document.createElement('input');
                    cellInput.type = 'text';
                    cellInput.classList.add('modal-parameters-table-input');
                    cellInput.value = rowData[header] || '';
                    if (attribute.parametersTable.dropdown_box_values && attribute.parametersTable.dropdown_box_values[header]) {
                        // Convert input to dropdown if dropdown values exist for this header
                        const dropdown = document.createElement('select');
                        dropdown.classList.add('modal-parameters-table-select');
                        attribute.parametersTable.dropdown_box_values[header].forEach(option => {
                            const optionElement = document.createElement('option');
                            optionElement.value = option;
                            optionElement.textContent = option;
                            dropdown.appendChild(optionElement);
                        });
                        dropdown.value = rowData[header] || '';
                        cellInput.replaceWith(dropdown);
                        cell.appendChild(dropdown);
                    } else {
                        cell.appendChild(cellInput);
                    }
                    row.appendChild(cell);
                });

                // Add remove button cell
                const removeCell = document.createElement('td');
                removeCell.classList.add('modal-parameters-table-cell');
                const removeButton = document.createElement('button');
                removeButton.type = 'button';
                removeButton.textContent = 'X';
                removeButton.classList.add('modal-remove-row-button');
                removeButton.onclick = () => row.remove(); // Removes the row when clicked
                removeCell.appendChild(removeButton);
                row.appendChild(removeCell);

                table.appendChild(row);
            });

            // Add the "Add Parameter" button to all tables
            const addRowButton = document.createElement('button');
            addRowButton.type = 'button';
            addRowButton.textContent = "Add Parameter";
            addRowButton.classList.add('modal-add-row-button');
            addRowButton.onclick = () => {
                const row = document.createElement('tr');
                attribute.parametersTable.headers.forEach(header => {
                    const cell = document.createElement('td');
                    cell.classList.add('modal-parameters-table-cell');

                    if (attribute.parametersTable.sequence_values && Object.keys(attribute.parametersTable.sequence_values).includes(header.toLowerCase())) {
                        // Sequence value logic
                        const column = Object.keys(attribute.parametersTable.sequence_values)[0];
                        let value = attribute.parametersTable.sequence_values[column]++;
                        const sequenceInput = document.createElement('input');
                        sequenceInput.type = 'number';
                        sequenceInput.value = value;
                        sequenceInput.classList.add('modal-parameters-table-input');
                        sequenceInput.onkeydown = allowOnlyNumbers;

                        cell.appendChild(sequenceInput);
                    } else if (attribute.parametersTable.dropdown_box_values && attribute.parametersTable.dropdown_box_values[header]) {
                        // Dropdown box logic
                        const dropdown = document.createElement('select');
                        dropdown.classList.add('modal-parameters-table-select');
                        attribute.parametersTable.dropdown_box_values[header].forEach(option => {
                            const optionElement = document.createElement('option');
                            optionElement.value = option;
                            optionElement.textContent = option;
                            dropdown.appendChild(optionElement);
                        });
                        cell.appendChild(dropdown);
                    } else {
                        // Default to a text input for other cases
                        const cellInput = document.createElement('input');
                        cellInput.type = 'text';
                        cellInput.classList.add('modal-parameters-table-input');
                        cell.appendChild(cellInput);
                    }

                    row.appendChild(cell);
                });

                // Add remove button cell
                const removeCell = document.createElement('td');
                removeCell.classList.add('modal-parameters-table-cell');
                const removeButton = document.createElement('button');
                removeButton.type = 'button';
                removeButton.textContent = 'X';
                removeButton.classList.add('modal-remove-row-button');
                removeButton.onclick = () => row.remove(); // Removes the row when clicked
                removeCell.appendChild(removeButton);
                row.appendChild(removeCell);

                table.appendChild(row);
            };

            tableContainer.appendChild(table);
            tableContainer.appendChild(addRowButton);
            input = tableContainer;
        } else if (attribute.freeTextArea) {
            // Free text area
            input = document.createElement('textarea');
            input.rows = 4;
            input.classList.add('modal-textarea');
        } else if (attribute.number) {
            // Number input
            input = document.createElement('input');
            input.type = 'number';
            input.min = '0';
            input.value = '200';
            input.step = '10';
            input.onkeydown = allowOnlyNumbers;
            input.classList.add('modal-number-input');
        } else {
            // Default to a text input for other cases
            input = document.createElement('input');
            input.type = 'text';
            input.classList.add('modal-text-input');
        }

        // Assign unique name for form data identification
        input.name = `${baseName}_${attribute.name}`;
        container.appendChild(questionLabel);
        container.appendChild(input);

        // Handle recursive `additionalAttribute`
        if (attribute.additionalAttribute) {
            const toggleAdditionalInputs = () => {
                const isVisible = input.value === attribute.additionalAttribute.conditional;
                nestedInputsContainer.style.display = isVisible ? 'block' : 'none';
            };

            // Create nested container for additional attributes
            const nestedInputsContainer = document.createElement('div');
            nestedInputsContainer.classList.add('nested-attribute-container');
            nestedInputsContainer.style.display = 'none'; // Initially hidden
            const nestedInputs = createAttributeInputs(
                attribute.additionalAttribute.attribute,
                modIndex,
                elemIndex,
                `${baseName}_${attribute.name}`,
                node
            );
            nestedInputsContainer.appendChild(nestedInputs);
            container.appendChild(nestedInputsContainer);

            // Add event listener for toggle logic
            input.addEventListener('change', toggleAdditionalInputs);

            // Ensure the visibility is set correctly on initial load
            toggleAdditionalInputs();
        }
        return container;
    }

    // Process modifications and generate form
    modifications.forEach((modification, modIndex) => {
        const elements = evaluateXPath(xmlDoc, modification.xpath);

        elements.forEach((node, elemIndex) => {
            if (debug) {
                console.log("----------------------------------------------");
                console.log("Node: " + getNodeAttribute(node, "label"));
            }

            // Get 'label' and 'type' attributes for descriptive legends
            const type = node.getAttribute('type') || 'Unknown Type';
            const label = node.getAttribute('label') || `Element ${elemIndex + 1}`;
            if (debug) {
                console.log("Current Node: " + label)
            }

            // Retrieve parent information
            const mxCell = node.querySelector('mxCell');
            const parentId = mxCell ? mxCell.getAttribute('parent') : null;
            if (debug) {
                console.log("ParentNodeID: " + parentId)
            }
            let parentLabel = '';

            if (parentId && parentId !== "1") {
                // Find the initial parent node
                let currentParentNode = xmlDoc.querySelector(`object[id="${parentId}"]`);
                if (debug) {
                    console.log("ParentNode: " + currentParentNode.getAttribute("type"))
                }

                // Traverse ancestry if the parent isn't a "cps_component"
                while (currentParentNode) {
                    const parentType = currentParentNode.getAttribute('type');

                    if (parentType === "cps_component") {
                        // If it's a cps_component, retrieve its label
                        parentLabel = currentParentNode.getAttribute('label') || '';
                        break;
                    } else if (parentType === "boundary") {
                        // Handle "boundary" by finding an "owns" relationship
                        // Get all 'object' elements with type="owns"
                        // Get the ID of the current parent node
                        const targetId = currentParentNode.getAttribute("id");

                        // Get all 'object' elements with type="owns"
                        const objects = xmlDoc.querySelectorAll('object[type="owns"]');

                        let ownsEdge = null;

                        // Loop through and find the correct object
                        objects.forEach(obj => {
                            const mxCell = obj.querySelector(`mxCell[target="${targetId}"]`);
                            if (mxCell) {
                                ownsEdge = obj; // Found the matching object
                            }
                        });

                        // Log or use the `ownsEdge`
                        if (ownsEdge) {
                            console.log('Found node:', ownsEdge);
                        } else {
                            console.log('No matching node found.');
                        }

                        if (ownsEdge) {
                            // Move to the next node in the relationship
                            // Get the child mxCell of the ownsEdge node
                            const mxCell = ownsEdge.querySelector('mxCell');

                            if (mxCell) {
                                // Get the 'source' attribute of the mxCell
                                const sourceId = mxCell.getAttribute('source');
                                console.log('Source ID:', sourceId);
                                currentParentNode = xmlDoc.querySelector(`object[id="${sourceId}"]`);
                                console.log("True parent: "+currentParentNode.getAttribute("label"));
                                parentLabel = currentParentNode.getAttribute("label");
                            } else {
                                console.log('No mxCell found as a child of ownsEdge.');
                            }

                            
                        } else {
                            // Stop if no valid "owns" edge is found
                            currentParentNode = null;
                        }
                    } else {
                        // For other types, stop the search
                        currentParentNode = null;
                    }
                }
            }


            // Compose the legend text
            //const legendText = parentLabel
            //    ? `${parentLabel} > ${type.charAt(0).toUpperCase() + type.slice(1)}: ${label}`
            //    : `${type.charAt(0).toUpperCase() + type.slice(1)}: ${label}`;
            
            //-----------------------------------------------------------------------------------
            /**
            * 🛠️ User-facing type label mapping (customization layer)
            * 
            * This map customizes the display names of element types in the form shown
            * during the PIM → PSM transformation. It only affects the GUI (not the model logic).
            * 
            * To change the label for a construct, uncomment its entry and provide a new value.
            * Keys must match the lowercase 'type' value used internally in the XML model.
            * 
            * Available types you may customize:
            *  - operational_goal
            *  - action
            *  - hw_resource
            *  - sw_resource
            *  - comm_thread
            *  - comm_listener
            *  - and_refinement_operator
            *  - or_refinement_operator
            *  - relation
            *  - comm_relation
            *  - cpc_container
            */

            const typeLabelMap = {
                "operational_goal": "on interval action",
                "action": "on demand action",
                "comm_thread": "message sender",
                "comm_listener": "message receiver",
                "cpc_container": "cp component"
                
                // To customize more types, just uncomment and rename as desired:
                // "hw_resource": "hw_resource",
                // "sw_resource": "sw_resource",
                // "and_refinement_operator": "and_ref",
                // "or_refinement_operator": "or_ref",
                // "relation": "rel",
                // "comm_relation": "comm_rel"
            };


            // Normalizes the type by removing any suffix or additional description.
            const baseType = type.split(":")[0].trim().toLowerCase(); // e.g., "Comm_thread: Dato ..." → "comm_thread"
            const readableType = typeLabelMap[baseType] || baseType;
            const legendText = parentLabel
                ? `${parentLabel} > ${readableType}: ${label}`
                : `${readableType}: ${label}`;
            //-----------------------------------------------------------------------------------


            // Create and style fieldset with legend
            const fieldset = document.createElement('fieldset');
            fieldset.classList.add('modal-fieldset');
            const legend = document.createElement('legend');
            legend.textContent = legendText;
            legend.classList.add('modal-legend');
            fieldset.appendChild(legend);

            modification.attributes.forEach(attribute => {
                // Check conditions for this specific attribute
                let conditionsMet = true;

                if (attribute.conditional) {
                    const conditionalAttribute = Object.keys(attribute.conditional)[0];
                    const conditionalValue = attribute.conditional[conditionalAttribute];

                    if (debug) {
                        console.log("----------------------------------------------");
                        console.log("Node: " + getNodeAttribute(node, "label"));
                        console.log("Attribute Name: " + attribute.name);
                        console.log("Conditional attribute: " + conditionalAttribute);
                        console.log("True Value: " + getNodeAttribute(node, conditionalAttribute));
                        console.log("Conditional Value: " + conditionalValue);
                    }

                    conditionsMet = getNodeAttribute(node, conditionalAttribute) === conditionalValue;

                    if (debug) {
                        console.log("Condition is met for attribute: " + conditionsMet);
                        console.log("----------------------------------------------");
                    }
                }

                // Only process the attribute if conditions are met
                if (conditionsMet) {
                    const baseName = `modification_${modIndex}_element_${elemIndex}`;
                    const attributeInputs = createAttributeInputs(attribute, modIndex, elemIndex, baseName, node);
                    fieldset.appendChild(attributeInputs);
                }
            });

            // Only append fieldset if it has children beyond the legend
            if (fieldset.children.length > 1) form.appendChild(fieldset);
        });
    });

}



// Utility to evaluate an XPath expression and return matching elements
function evaluateXPath(xmlDoc, xpath) {
    const results = [];
    const xpathResult = xmlDoc.evaluate(xpath, xmlDoc, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
    for (let i = 0; i < xpathResult.snapshotLength; i++) {
        results.push(xpathResult.snapshotItem(i));
    }
    return results;
}


// Handle the modal form submission
document.getElementById('submitAttributesBtn').addEventListener('click', function () {
    const formData = collectFormData();
    if (debug) {
        console.log("Form Data: " + JSON.stringify(formData));
    }

    if (jsonFiles.length > 0) {
        // Get modification rules from the first JSON file
        const modificationRules = JSON.parse(jsonFiles[0].content).modifications;
        let inputXML = document.getElementById('inputXML').value;

        if (modificationRules) {
            // Apply modifications using collected form data
            inputXML = applyModifications(inputXML, modificationRules, formData);

            // Update the input XML textarea with the modified XML
            document.getElementById('inputXML').value = inputXML;

            closeModal(); // Close modal after applying changes
            alert("Modifications applied successfully.");
        } else {
            alert("No valid modification rules found.");
        }
    } else {
        alert('No JSON files uploaded. Please upload a valid JSON file with rules.');
    }
});

// Function to collect all form data, including complex types
function collectFormData() {
    const formData = new FormData(document.getElementById('questionnaireForm'));
    const data = {};

    // Convert FormData to a plain object for easier handling
    formData.forEach((value, key) => {
        data[key] = value;
    });

    // Collect data from tables (parametersTable)
    document.querySelectorAll('.modal-parameters-table-container table').forEach(table => {
        const rows = Array.from(table.querySelectorAll('tr')).slice(1); // Exclude header row
        const headers = Array.from(table.querySelector('tr').querySelectorAll('th')).map(th => th.textContent.trim()); // Extract headers

        const tableData = rows.map(row => {
            const rowData = {};
            Array.from(row.querySelectorAll('td')).forEach((cell, index) => {
                // Use header as key if it exists and match to the cell value
                if (index < headers.length - 1) { // Exclude the last column (Remove button)
                    const header = headers[index].toLowerCase();
                    const input = cell.querySelector('input, select'); // Collect value from input or select
                    if (input) {
                        rowData[header] = input.value;
                    }
                }
            });
            return rowData;
        });

        // Store table data using table's unique ID as key
        data[table.id] = tableData;
    });

    // Collect data from conditional attributes
    document.querySelectorAll('textarea').forEach(textarea => {
        if (textarea.style.display !== 'none') { // Only include visible textareas
            data[textarea.name] = textarea.value;
        }
    });

    return data;
}

// Function to load preset files
async function loadPresetFiles(preset) {
    if (preset === "custom") {
        xsltFiles = [];
        jsonFiles = [];
        updateFileList(xsltFiles, 'xslFileList');
        updateFileList(jsonFiles, 'jsonFileList');
        return;
    }

    const presetData = PRESET_FILES[preset];

    // Load XSLT files
    xsltFiles = await Promise.all(
        presetData.xslt.map(path => fetch(path).then(res => res.text()).then(content => ({
            name: path.split('/').pop(),
            content
        })))
    );

    // Load JSON file
    const jsonContent = await fetch(presetData.json).then(res => res.text());
    jsonFiles = [{ name: presetData.json.split('/').pop(), content: jsonContent }];

    updateFileList(xsltFiles, 'xslFileList');
    updateFileList(jsonFiles, 'jsonFileList');
}

// Event listeners for preset radio buttons
document.getElementById('cimPimPreset').addEventListener('change', function () {
    if (this.checked) {
        currentPreset = "cim-pim";
        document.getElementById('xslFileUpload').style.display = "none";
        document.getElementById('jsonFileUpload').style.display = "none";
        document.getElementById('psmAttributeArea').style.display = "none";
        loadPresetFiles("cim-pim");
    }
});

document.getElementById('pimPSMPreset').addEventListener('change', function () {
    if (this.checked) {
        currentPreset = "pim-psm";
        document.getElementById('xslFileUpload').style.display = "none";
        document.getElementById('jsonFileUpload').style.display = "none";
        document.getElementById('psmAttributeArea').style.display = "flex";
        loadPresetFiles("pim-psm");
    }
});
/*
document.getElementById('customPreset').addEventListener('change', function () {
    if (this.checked) {
        currentPreset = "custom";
        document.getElementById('xslFileUpload').style.display = "flex";
        document.getElementById('jsonFileUpload').style.display = "flex";
        document.getElementById('psmAttributeArea').style.display = "none";
        loadPresetFiles("custom");
    }
});

*/

function allowOnlyNumbers(event) {
    // Define allowed keys
    const allowedKeys = ['Backspace', 'ArrowLeft', 'ArrowRight', 'Delete', 'Tab'];

    // Check if the pressed key is allowed
    if (
        !allowedKeys.includes(event.key) && // Allow navigation and editing keys
        (event.key < '0' || event.key > '9') // Block non-numeric keys
    ) {
        event.preventDefault();
    }
}

function capitalizeWord(word) {
    if (!word) return ''; // Handle empty strings gracefully
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
}


// Initial setup for default preset
loadPresetFiles(currentPreset);




