// Global variable to store the modification rules from the JSON file
let modificationRules = [];

// Function to handle JSON file upload
function handleJSONUpload(inputElement) {
    const file = inputElement.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            try {
                // Parse the JSON file content
                const json = JSON.parse(e.target.result);
                modificationRules = json.modifications;

                // Automatically populate the questionnaire if JSON is valid
                if (modificationRules.length > 0) {
                    populateQuestionnaireForm(modificationRules);
                    openModal(); // Open modal to display questionnaire
                } else {
                    alert("No modifications found in JSON."); // Inform user if no modifications
                }
            } catch (error) {
                alert("Invalid JSON format.");
                console.error("JSON parse error:", error);
            }
        };
        reader.readAsText(file);
    }
}




// Function to evaluate an XPath expression and return matching nodes
function evaluateXPath(xmlDoc, xpath) {
    const xpathResult = [];
    const evaluator = new XPathEvaluator();
    const result = evaluator.evaluate(xpath, xmlDoc, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);

    for (let i = 0; i < result.snapshotLength; i++) {
        xpathResult.push(result.snapshotItem(i));
    }
    return xpathResult;
}

