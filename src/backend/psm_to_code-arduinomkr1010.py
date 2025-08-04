import sys
import os
import json
from xml.etree import ElementTree as ET
import re

debug = True

# Define the type mapping for Arduino-supported types
type_mapping = {
    "int": {"arduino_type": "int", "default_value": "0"},
    "double": {"arduino_type": "double", "default_value": "0.0"},
    "string": {"arduino_type": "String", "default_value": '"default"'},  # Arduino String type
    "char[50]": {"arduino_type": "char", "default_value": '{"default"}', "is_array": True, "array_size": 50},  # C-style char array
    "bool": {"arduino_type": "bool", "default_value": "false"}
}

def strip_html_tags(text):
    if text:
        return re.sub(r"<.*?>", "", text)
    return text

def generate_data_extraction(listener_thread):
    data_structure_str = listener_thread.get("data_structure")
    fields = json.loads(data_structure_str)
    result = []
    for field in fields:
        result.append(f'{process_name(listener_thread.get("name"))}_data_structure.{process_name(field.get("name"))} = doc["{process_name(field.get("name"))}"];')
    result_str = "\n".join(result)
    return result_str

def generate_debug_listener_print(listener_thread):
    data_structure_str = listener_thread.get("data_structure")
    fields = json.loads(data_structure_str)
    result = []
    for field in fields:
        result.append(f'Serial.print("{process_name(field.get("name"))}: ");')
        result.append(f'Serial.println({process_name(listener_thread.get("name"))}_data_structure.{process_name(field.get("name"))});')
    result_str = "\n".join(result)
    return result_str

def generate_listener_thread_code(cpc):
    listener_threads = cpc.findall("listenerThread")
    result_str = ""
    
    # Create a listener thread for each listener_thread object
    for listener_thread in listener_threads:
        listener_name = process_name(listener_thread.get("name"))
        topic = f"{listener_name}_topic"
        timing = listener_thread.get("interval_in_milliseconds")
        listener_comments = apply_indentation_to_text(generate_listener_thread_comments(listener_thread, cpc), "    ")
        client = f"{listener_name}MqttClient"
        client_id = f"{listener_name}ClientId"
        
        # Listener thread function declaration
        result_str += f"""
void receiveDependum_{listener_name}Task(void *pvParameters) {{
{listener_comments}
    // This variable handles the period in milliseconds for thread execution
    const TickType_t xDelay = pdMS_TO_TICKS({timing});
    

    for (;;)
    {{

        // Check MQTT connection status
        if (!{client}.connected())
        {{
          connectToMQTT({client}, {client_id}, {topic});
        }}

        // Always poll MQTT for new messages
        {client}.loop();

        // Keep delay to avoid overloading loop but keep polling
        vTaskDelay(xDelay);
    }}
}}
"""
    return result_str


def generate_connection_to_topics(cpc):
    comm_threads = cpc.findall("commThread")
    listener_threads = cpc.findall("listenerThread")
    
    variables_array = []
    if(comm_threads):
        variables_array.append("// Connection and subscription to topics(Sender)")

        for comm_thread in comm_threads:
            comm_thread_client = f'{process_name(comm_thread.get("name"))}MqttClient'
            comm_thread_client_id = f'{process_name(comm_thread.get("name"))}ClientId'
            variables_array.append(f'mqttSetup({comm_thread_client});')
            variables_array.append(f'connectToMQTT({comm_thread_client}, {comm_thread_client_id}, {process_name(comm_thread.get("name"))}_topic);')
    
    if(listener_threads):
        variables_array.append("// Listener Topics(Receiver)")

        for listener_thread in listener_threads:
            listener_thread_client = f'{process_name(listener_thread.get("name"))}MqttClient'
            listener_thread_client_id = f'{process_name(listener_thread.get("name"))}ClientId'
            variables_array.append(f'mqttSetup({listener_thread_client}, callback_{process_name(listener_thread.get("name"))});')
            variables_array.append(f'connectToMQTT({listener_thread_client}, {listener_thread_client_id}, {process_name(listener_thread.get("name"))}_topic);')

    result_str = "\n".join(variables_array)
    return result_str

def generate_listener_thread_comments(listener_thread, cpc):
    # Extract basic attributes
    listener_thread_name = listener_thread.get("name")
    listener_thread_id = listener_thread.get("id")
    original_element = listener_thread.get("name")  # Assuming the original element matches the name
    transformed_function = f'{process_name(listener_thread_name)}()'  # Transform to function name format
    qualification_array = listener_thread.get("qualification_array")
    contribution_array = listener_thread.get("contribution_array")
    dependum = f'{process_name(listener_thread.get("name"))}_data_structure'

    dependerRelation = cpc.find(".//commRelation[@source='" + listener_thread_id + "']")
    dependerObject = cpc.find((".//*[@id='" + dependerRelation.get("target") + "']"))
    dependerName = dependerObject.get("name")
    dependerType = dependerObject.tag
    dependerStatement=""
    if(dependerType == "function"):
        dependerStatement += f"function {process_name(dependerName)}()"
    elif(dependerType == "thread"):
        dependerStatement += f"thread {process_name(dependerName)}()"
    elif(dependerType == "hw_resource"):
        dependerStatement += f'hardware resource "{process_name(dependerName)}"()'
    elif(dependerType == "sw_resource"):
        dependerStatement += f'software resource "{process_name(dependerName)}_data_structure"()'
    
    # Prepare the qualification array comment (if present)
    qualification_comment = ""
    if qualification_array:
        qualifications = qualification_array.split(";")
        qualification_comment = "\n".join(
            f" * - \"{qual.strip()}\"" for qual in qualifications
        )
    else:
        qualification_comment = " * None specified."

    # Prepare the contribution array comment (if present)
    contribution_comment = ""
    if contribution_array:
        contributions = contribution_array.split(";")
        contribution_comment = "\n".join(
            f" * - \"{contrib.strip()}\"" for contrib in contributions
        )
    else:
        contribution_comment = " * None specified."


    # Generate the comment block
    comments = f"""
//
// --- Listener Thread Information ---
// Name: {listener_thread_name}
// ID: {listener_thread_id}
// Description: This Listener Thread is responsible for receiving the dependum: {dependum}
//
// Original Element in PIM: {original_element}
// Transformed To: Function `{transformed_function}`
//
// Note for Developers:
// The `dependum` data should be stored on and then retrieved from the {dependerStatement}.
// Ensure the function completes its operation and receives the required data 
// in the appropriate format for reception.
// 
// Qualification Array:
// {qualification_comment}
// 
// Contribution Array:
// {contribution_comment}
// 
//
"""
    comments = apply_indentation_to_text(comments, indent_str="    ")
    return comments

def generate_comm_thread_comments(comm_thread, cpc):
    # Extract basic attributes
    comm_thread_name = comm_thread.get("name")
    comm_thread_id = comm_thread.get("id")
    original_element = comm_thread.get("name")  # Assuming the original element matches the name
    transformed_function = f"{process_name(comm_thread_name)}()"  # Transform to function name format
    qualification_array = comm_thread.get("qualification_array")
    contribution_array = comm_thread.get("contribution_array")
    dependum = f'{process_name(comm_thread.get("name"))}_data_structure'

    dependeeRelation = cpc.find(".//commRelation[@target='" + comm_thread_id + "']")
    dependeeObject = cpc.find((".//*[@id='" + dependeeRelation.get("source") + "']"))
    dependeeName = dependeeObject.get("name")
    dependeeType = dependeeObject.tag
    dependeeStatement=""
    if(dependeeType == "function"):
        dependeeStatement += f"function {process_name(dependeeName)}()"
    elif(dependeeType == "thread"):
        dependeeStatement += f"thread {process_name(dependeeName)}()"
    elif(dependeeType == "hw_resource"):
        dependeeStatement += f'hardware resource "{process_name(dependeeName)}"()'
    elif(dependeeType == "sw_resource"):
        dependeeStatement += f'software resource "{process_name(dependeeName)}_data_structure"()'
    
    # Prepare the qualification array comment (if present)
    qualification_comment = ""
    if qualification_array:
        qualifications = qualification_array.split(";")
        qualification_comment = "\n".join(
            f" * - \"{qual.strip()}\"" for qual in qualifications
        )
    else:
        qualification_comment = " * None specified."

    # Prepare the contribution array comment (if present)
    contribution_comment = ""
    if contribution_array:
        contributions = contribution_array.split(";")
        contribution_comment = "\n".join(
            f" * - \"{contrib.strip()}\"" for contrib in contributions
        )
    else:
        contribution_comment = " * None specified."


    # Generate the comment block
    comments = f"""
//
// --- Comm Thread Information ---
// Name: {comm_thread_name}
// ID: {comm_thread_id}
// Description: This Comm Thread is responsible for generating the dependum: {dependum}
//
// Original Element in PIM: {original_element}
// Transformed To: Function `{transformed_function}`
//
// Note for Developers:
// The `dependum` data should be generated by the {dependeeStatement}.
// Ensure the function completes its operation and provides the required data 
// in the appropriate format for transmission.
// 
// Qualification Array:
// {qualification_comment}
// 
// Contribution Array:
// {contribution_comment}
// 
//
"""
    comments = apply_indentation_to_text(comments, indent_str="    ")
    return comments


def generate_json_comm_data_structure(comm_thread):
    data_structure_str = comm_thread.get("data_structure")
    fields = json.loads(data_structure_str)
    result = []
    for field in fields:
        result.append(f'dependumJson["{process_name(field.get("name"))}"] = {process_name(comm_thread.get("name"))}_data_structure.{process_name(field.get("name"))};')
    result_str = "\n".join(result)
    return result_str

def generate_comm_thread_handles(cpc):
    comm_threads = cpc.findall("commThread")
    result = []
    for comm_thread in comm_threads:
        result.append(f'TaskHandle_t TaskpublishDependum_{process_name(comm_thread.get("name"))};')

    result_str = "\n".join(result)
    return result_str

def generate_listener_thread_handles(cpc):
    listener_threads = cpc.findall("listenerThread")
    result = []
    for listener_thread in listener_threads:
        result.append(f'TaskHandle_t TaskreceiveDependum_{process_name(listener_thread.get("name"))};')

    result_str = "\n".join(result)
    return result_str

def generate_comm_threads(cpc, debug=False):
    comm_threads_content = ""

    # Get all comm_thread objects from the cpc
    comm_threads = cpc.findall("commThread")
    
    for comm_thread in comm_threads:
        # Extract information from each commThread
        comm_thread_id = comm_thread.get("id")
        comm_thread_name = comm_thread.get("name")
        comm_thread_timing = comm_thread.get("interval_in_milliseconds")
        comm_thread_comments = generate_comm_thread_comments(comm_thread, cpc)
        data_structure = apply_indentation_to_text(generate_json_comm_data_structure(comm_thread), indent_str="        ")
        operation_modes = generate_operation_mode_switch(comm_thread, indentation="    ")
        client = f"{process_name(comm_thread_name)}MqttClient"
        
        
        if debug:
            print(f"CommThread ID: {comm_thread_id}")
            print(f"CommThread Name: {comm_thread_name}")

        # Prepare the communication topic
        topic = f"{process_name(comm_thread_name)}_topic"

        # Generate the code for the Dependum struct and publish function
        comm_thread_code = f"""

void publishDependum_{process_name(comm_thread_name)}Task(void *pvParameters) {{
{comm_thread_comments}
    // This variable handles the period in milliseconds for thread execution
    const TickType_t xDelay = pdMS_TO_TICKS({comm_thread_timing});
    for (;;) {{
        // Create a JSON object for the dependum
        JSONVar dependumJson;
{data_structure}

        // Convert the JSON object to a string
        String dependumMessage = JSON.stringify(dependumJson);

{operation_modes}

        {client}.publish({topic}, dependumMessage.c_str());  // Publish message
        if (debug) {{
            Serial.println("Dependum published successfully for {comm_thread_name}!");
            Serial.print("Topic: ");
            Serial.println({topic});
            Serial.print("Message: ");
            Serial.println(dependumMessage);
        }} else {{
            if (debug) {{
                Serial.println("Failed to publish dependum for {comm_thread_name}.");
            }}
            
        }}
        vTaskDelay(xDelay);
    }}
}}
"""
        # Add the generated code to the comm_threads_content
        comm_threads_content += comm_thread_code + "\n"

    return comm_threads_content


def generate_listener_threads(cpc):
    listener_threads_content = ""
    return listener_threads_content

def generate_all_comm_mqtt_ids(cpc):
    comm_threads = cpc.findall("commThread")
    listener_threads = cpc.findall("listenerThread")
    
    variables_array = []
    if(comm_threads):
        variables_array.append("// Comm Topics(Sender)")

        for comm_thread in comm_threads:
            variables_array.append(f'const char* {process_name(comm_thread.get("name"))}_topic = "{CPS_id}/{process_name(cpc.get("id"))}/{process_name(comm_thread.get("id"))}/dependum";')
    
    if(listener_threads):
        variables_array.append("// Listener Topics(Receiver)")

        for listener_thread in listener_threads:
            variables_array.append(f'const char* {process_name(listener_thread.get("name"))}_topic = "{CPS_id}/{process_name(listener_thread.get("comm_threadCPCId"))}/{process_name(listener_thread.get("comm_threadId"))}/dependum";')

    comm_str = "\n".join(variables_array)

    if(debug):
        print("Comm variables String: ", comm_str)
    
    return comm_str
    

def apply_indentation_to_text(text, indent_str="    "):
    """
    Apply a given indentation to each line of a multi-line text block.

    Args:
        text (str): The text to which the indentation will be applied.
        indent_str (str): The string representing the indentation (e.g., "    ").

    Returns:
        str: The indented text.
    """
    # Split the text into lines, apply the indentation, and join back into a single string
    return "\n".join([indent_str + line if line.strip() else line for line in text.splitlines()])


def generate_data_structure(obj, variableMode):
    """
    Generate an Arduino struct declaration from the data_structure or dependum_data_structure attribute.

    Parameters:
    - obj: The object containing the data_structure or dependum_data_structure attributes.

    Returns:
    - A string containing the generated struct declaration.
    """
    # Determine the source of the data structure
    data_structure = obj.get("data_structure")
    if not data_structure:
        data_structure = obj.get("dependum_data_structure", "[]")

    # Parse the JSON content
    try:
        fields = json.loads(data_structure)
    except json.JSONDecodeError:
        return "// Error: Invalid data structure format\n"

    # Ensure fields contain keys required by generateVariables
    for field in fields:
        # Normalize keys to match expected format in type_mapping
        field["name"] = field.get("name", field.get("name", "UnknownName"))
        field["description"] = field.get("description", field.get("description", "No description available."))
        field["type"] = field.get("type", "double")  # Default to "double" if type is not provided

    # Determine the struct name
    struct_name = f"{process_name(obj.get('name'))}_data_structure"

    # Start building the struct definition
    struct_declaration = [f"struct {struct_name} {{\n"]

    # Use generateVariables to define each field in the struct
    temp_output = []
    generateVariables(
        params=fields,
        object_name="",  # Struct variables don't use a prefix
        output_str=temp_output,
        indentation_space="    ",  # Structs use 4 spaces as indentation
        mode=variableMode  # Use the initialization logic to define variables
    )

    # Add generated fields to the struct
    struct_declaration.extend(temp_output)

    # Close the struct definition
    struct_declaration.append(f"}} {struct_name};\n")

    return "".join(struct_declaration)

def generate_object_data_structures(obj, mode):
    # Generate the data structure for the current object
    struct_code = generate_data_structure(obj, mode)
    return struct_code


def generate_all_data_structures(cpc, mode):
    """
    Generate Arduino struct declarations for applicable objects in cpc.

    Parameters:
    - cpc: The root XML element containing objects like "commThread", "listenerThread", and "sw_resource".

    Returns:
    - A string containing all generated struct declarations.
    """
    # Object types to process
    object_types = ["commThread", "listenerThread", "sw_resource"]

    # Collect all struct declarations
    struct_declarations = []

    # Iterate through each object type
    for obj_type in object_types:
        # Find all objects of the given type
        objects = cpc.findall(obj_type)
        for obj in objects:
            # Generate the data structure for the current object
            struct_declarations.append(generate_object_data_structures(obj, mode))

    # Join all struct declarations into a single string
    return "\n".join(struct_declarations)

def declare_operation_mode_variables(cpc):
    # Supported element types
    element_types = ["thread", "commThread", "listenerThread"]
    declarations = []

    for element_type in element_types:
        elements = cpc.findall(element_type)

        for element in elements:
            # Check if operation modes are enabled
            operation_modes_enabled = element.get("operation_modes_enabled", "false") == "true"
            if not operation_modes_enabled:
                continue

            # Parse operation modes
            operation_modes = json.loads(element.get("operation_modes", "[]"))
            if not operation_modes:
                continue

            # Get the name of the element and process it
            element_name = process_name(element.get("name"))
            operation_mode_var = f"{element_name}_operation_mode"

            # Initialize the variable to the first mode's code
            first_mode_code = operation_modes[0]["code"]

            # Generate the declaration line
            declarations.append(f"int {operation_mode_var} = {first_mode_code}; // Initial operation mode: {operation_modes[0]['name']}")

    return "\n".join(declarations)


def generate_operation_mode_switch(obj, indentation="    "):
    """
    Generates a switch statement for operation modes with customizable indentation.

    Parameters:
    - obj: The object (function, thread, etc.) containing the operation modes.
    - indentation: The string to be used for indentation (default is 4 spaces).

    Returns:
    - A string containing the generated switch statement for operation modes.
    """
    # Check if operation modes are enabled
    operation_modes_enabled = obj.get("operation_modes_enabled", "false") == "true"
    if not operation_modes_enabled:
        return ""

    # Parse operation modes
    operation_modes = json.loads(obj.get("operation_modes", "[]"))
    operation_mode_var = f"{process_name(obj.get('name'))}_operation_mode"

    # Start the switch structure with the specified indentation
    operation_mode_switch = f"\n{indentation}switch ({operation_mode_var}) {{\n"
    
    # Generate cases for each operation mode
    for mode in operation_modes:
        mode_code = mode["code"]
        mode_name = mode["name"]
        mode_description = mode["description"]

        operation_mode_switch += f"{indentation}    case {mode_code}: // {mode_name} - {mode_description}\n"
        operation_mode_switch += f"{indentation}        // Your logic for {mode_name} goes here\n"
        operation_mode_switch += f"{indentation}        break;\n"
    
    # Default case
    operation_mode_switch += f"{indentation}    default:\n"
    operation_mode_switch += f"{indentation}        // Handle undefined operation modes\n"
    operation_mode_switch += f"{indentation}        break;\n"
    
    # Close the switch statement
    operation_mode_switch += f"{indentation}}}\n"

    return operation_mode_switch

def generateVariables(params, object_name, output_str, indentation_space, mode):
    for param in params:
        # Retrieve type information from type_mapping
        type_info = type_mapping.get(param['type'], {"arduino_type": param['type'], "default_value": "", "is_array": False})
        arduino_type = type_info["arduino_type"]
        is_array = type_info.get("is_array", False)
        array_size = type_info.get("array_size", None)
        default_value = type_info["default_value"] if type_info["default_value"] else ""

        if debug:
            print("Type info:\n  ", type_info)

        # Generate the variable name with function name prefix
        variable_name = f"{object_name}_{process_name(param['name'])}" if object_name.strip() else f"{process_name(param['name'])}"
        variable_description = param['description']

        # Handle array types (e.g., char[50]) and non-array types
        if is_array and array_size:  # Handle array types like char[50]
            if mode == "init":
                # Handle default value
                output_str.append(f"{indentation_space}{arduino_type} {variable_name} = {default_value}; // {variable_description}\n")
            elif mode == "assign":
                # Only include assignment if there's a default value
                if default_value:
                    output_str.append(f"{indentation_space}strcpy({variable_name}, {type_info['default_value']}); // {variable_description}\n")
            elif mode == "declare":
                # Just declare the array with the correct size
                output_str.append(f"{indentation_space}{arduino_type} {variable_name}[{array_size}]; // {variable_description}\n")
        else:  # Handle non-array types
            if mode == "init":
                # Include type declaration and default value
                default_value_str = f" = {default_value}" if default_value else ""
                output_str.append(f"{indentation_space}{arduino_type} {variable_name}{default_value_str}; // {variable_description}\n")
            elif mode == "assign":
                # Only include assignment if there's a default value
                if default_value:
                    output_str.append(f"{indentation_space}{variable_name} = {default_value}; // {variable_description}\n")
            elif mode == "declare":
                # Just declare the variable
                output_str.append(f"{indentation_space}{arduino_type} {variable_name}; // {variable_description}\n")


def process_name(raw_name):
    words = raw_name.split()
    processed_name = words[0].lower() + ''.join(word.capitalize() for word in words[1:])
    processed_name = processed_name.replace("-","_")
    return processed_name

def write_to_file(directory, file_name, content, file_type):
    """
    Write content to a file, with support for different file types ('.ino', '.h').
    """
    file_path = os.path.join(directory, file_name + file_type)
    with open(file_path, 'w') as file:
        file.write(content)
    print(f"Generated {file_name}{file_type} in {directory}")

def generate_secrets_file(directory):
    """
    Generate the secrets.h file with placeholder WiFi and MQTT credentials.
    """
    secrets_content = '''\
// WiFi credentials
#define SECRET_SSID "your_SSID"      // Replace with your WiFi SSID
#define SECRET_PASS "your_PASSWORD"  // Replace with your WiFi password

// MQTT server settings
#define SECRET_MQTT_BROKER "broker.hivemq.com"  // Example public MQTT broker
#define SECRET_MQTT_PORT 1883                  // Standard MQTT port
'''
    write_to_file(directory, "secrets", secrets_content, ".h")

def generate_comm_utils_file(directory):
    """
    Generate the comm_utils.h file with functions for WiFi and MQTT connectivity.
    """
    comm_utils_content = '''\
#include <WiFiNINA.h>
#include <PubSubClient.h>
#include "secrets.h"

// Function to initialize Wi-Fi
void connectToWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(SECRET_SSID, SECRET_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }

  Serial.println("Connected to WiFi!");
}

// Function to initialize MQTT with optional callback
void mqttSetup(PubSubClient &client, MQTT_CALLBACK_SIGNATURE = nullptr) {
  client.setServer(SECRET_MQTT_BROKER, SECRET_MQTT_PORT);
  if (callback != nullptr) {
      client.setCallback(callback); // Set callback only if provided
  }
}

// Function to establish an MQTT connection
void connectToMQTT(PubSubClient &client, const char* clientId, const char* topic) {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(clientId)) {
      Serial.println("Connected to MQTT broker!");
      client.subscribe(topic);
    } else {
      Serial.print("Failed. Retrying in 1 second...");
      delay(1000);
    }
  }
}

'''
    write_to_file(directory, "comm_utils", comm_utils_content, ".h")

def generate_hw_resource_comments(function, cpc):
    """
    Generate comments for hardware resources assigned to the given function.
    This will check for <relation> elements where the function's id is the target,
    and generate comments about the associated hardware resources.

    Parameters:
    - function: The <function> element for which to generate the hardware resource comments.
    - cpc: The <cpc> element that contains the hardware resources and relations.

    Returns:
    - A string containing the hardware resource comments.
    """
    # Initialize the comments string
    hw_resource_comments = ""

    # Get the function's id
    function_id = function.get("id")

    # Find all <relation> elements in the cpc where the function's id is the target
    relations = cpc.findall(".//relation[@target='" + function_id + "']")

    # Iterate over the relations to get the source (hw_resource) ids
    hw_resource_ids = [relation.get("source") for relation in relations]

    hw_resource_comments += "// Hardware Resource Assigned:\n"

    # For each hw_resource_id, find the corresponding <hw_resource> and generate comments
    for hw_resource_id in hw_resource_ids:
        hw_resource = cpc.find(".//hw_resource[@id='" + hw_resource_id + "']")
        if hw_resource is not None:
            hw_resource_name = strip_html_tags(hw_resource.get("name"))
            hw_resource_parent_id = hw_resource.get("id_cim_parent")
            hw_resource_description = hw_resource.get("integration_operation_description")
            hw_resource_comments += f"""\
    // {hw_resource_name}:
    //     ID: {hw_resource_id}
    //     Parent ID: {hw_resource_parent_id}
    //     Description: {hw_resource_description}
"""
    
    return hw_resource_comments

def generate_function_code(function, cpc):
    """
    Generate the function code for a given <function> object, including comments for
    hardware resources assigned to it, and adding support for operation modes.
    """
    # Extract function attributes
    function_name = process_name(function.get("name"))
    function_id = function.get("id")
    function_parent = function.get("id_cim_parent")

    # Parse input and output parameters from JSON strings
    input_params = json.loads(function.get("input_parameters"))
    output_params = json.loads(function.get("output_parameters"))

    # Build function signature
    func_signature = f"bool {function_name}("
    input_param_str = []

    for param in input_params:
        # Retrieve the type information from the type_mapping dictionary
        type_info = type_mapping.get(param['type'], {"arduino_type": param['type']})  # Fallback to the original type if not found
        arduino_type = type_info["arduino_type"]
        
        # Process the parameter name and append to the input parameter string
        param_name = process_name(param["name"])
        input_param_str.append(f"{arduino_type} {param_name}")
    
    if(function.get("operation_modes_enabled")=="true"):
        json_operation_modes = json.loads(function.get('operation_modes'))
        default_mode = json_operation_modes[0]["code"]
        input_param_str.append(f"int {process_name(function.get('name'))}_operation_mode = {default_mode}")

    func_signature += ", ".join(input_param_str) + ") {"

    # Prepare function comments inside the function body
    func_comments = f"""\
    // Function ID: {function_id}
    // Parent ID: {function_parent}
    """
    func_comments += "// Input Parameters:\n"
    for param in input_params:
        func_comments += f"        // {param['name']}({param['type']}) - {param['description']}\n"
    
    func_comments += "    // Output Parameters:\n"
    for param in output_params:
        func_comments += f"        // {param['name']}({param['type']}) - {param['description']}\n"

    # Add qualification and contribution arrays as comments
    qualification_array = function.get("qualification_array")
    contribution_array = function.get("contribution_array")
    qualification_comment = ""
    if qualification_array.replace("[]",""):
        qualifications = qualification_array.split(";")
        qualification_comment = "\n".join(
            f" * - \"{qual.strip()}\"" for qual in qualifications
        )
    else:
        qualification_comment = " * None specified."
    # Prepare the contribution array comment (if present)
    contribution_comment = ""
    if contribution_array.replace("[]",""):
        contributions = contribution_array.split(";")
        contribution_comment = "\n".join(
            f" * - \"{contrib.strip()}\"" for contrib in contributions
        )
    else:
        contribution_comment = " * None specified."

    func_comments += f'''    // Qualification Array:
    // {qualification_comment}
'''
    
    func_comments += f'''    // Contribution Array:
    // {contribution_comment}
'''

    # Generate comments for hardware resources assigned to this function
    hw_resource_comments = apply_indentation_to_text(generate_hw_resource_comments(function, cpc), "    ")
    func_comments += hw_resource_comments

    # Generate output parameter declarations
    output_param_str = []
    generateVariables(output_params, function_name, output_param_str, "   ", "assign")

    # Generate operation mode switch (if applicable)
    operation_mode_switch = generate_operation_mode_switch(function)

    # Get all sw_resource objects and check for relations to the current function
    sw_resources = cpc.findall("sw_resource")
    if debug:
        print("SW Resources: ", sw_resources)

    related_sw_resources = []

    for sw_resource in sw_resources:
        # Find relations where the 'source' is the sw_resource id and the 'target' is the function id
        if debug:
            print("SW Resource ID: ", sw_resource.get('id'))
            print("Function ID: ", function_id)

        # Assuming cpc is an ElementTree object representing your XML document
        relations = cpc.findall(f".//relation[@source='{sw_resource.get('id')}'][@target='{function_id}']")

        if relations:
            # If there's a relation, add the sw_resource to the list of related resources
            related_sw_resources.append(sw_resource)

    if debug:
        print("SW Resource relations: ", related_sw_resources)

    # Generate data structures for the related sw_resources
    sw_resource_structs = ""
    for sw_resource in related_sw_resources:
        # Extract struct name and members
        if(debug):
            print("SW Name: ",process_name(sw_resource.get("name")));

        struct_name = process_name(sw_resource.get("name"))  # e.g., resourceB_data_structure
        data_structure_json = sw_resource.get("data_structure")
        
        # Parse JSON string into Python dictionary
        data_structure = json.loads(data_structure_json) if data_structure_json else []

        # Generate struct initialization code
        struct_init = ""
        sw_name = sw_resource.get("name")
        # Generate comments regarding the SW Resource used
        sw_comments = f'''
// This function uses the software resource: {sw_name}
// Using the Data Structure {(struct_name)}_data_structure\n
'''
        struct_init += apply_indentation_to_text(sw_comments, "    ")

        for member in data_structure:
            member_name = process_name(member["name"])  # Normalize member name
            member_type = member["type"].split('[')[0].strip()  # Extract base type (e.g., char, int)
            
            if member_type == "char":  # Handle string initialization
                struct_init += f'    strcpy({struct_name}_data_structure.{member_name}, "default");  // Initialize string member\n'
            else:  # Handle numeric initialization
                default_value = "0" if member_type in ["int", "float", "double"] else "0"  # Set default value for numbers
                struct_init += f"    {struct_name}_data_structure.{member_name} = {default_value};  // Initialize numeric member\n"
        
        sw_resource_structs += struct_init + "\n"  # Append the generated struct initialization

    # Generate the function body
    function_body = f"""
{func_signature}
{func_comments}
    // Set output parameters
 {' '.join(output_param_str)}
{sw_resource_structs}
    // --- Your code goes here ---
    
    {operation_mode_switch}
    
    return true;

    // --- Your code goes here ---
}}
"""

    if debug:
        print("Generated Function Body:\n", function_body)

    return function_body



def generate_thread_definitions(threads):
    """
    Generate global variables and task handles for threads.
    """
    definitions = ""
    for thread in threads:
        thread_id = thread.get("id")
        thread_name = process_name(thread.get("name"))
        definitions += f"bool {thread_name}_GoalAchieved = false; // Global variable for thread {thread_name}(ID: {thread_id})\n"
        definitions += f"TaskHandle_t Task{thread_name};\n"
    return definitions + "\n"


def generate_setup_task_creation(threads, comm_threads, listener_threads):
    """
    Generate task creation code for the setup() function.
    """
    setup_tasks = ""
    for thread in threads:
        thread_name = process_name(thread.get("name"))
        setup_tasks += f'''\
    xTaskCreate(
        {thread_name}Task,        // Function to implement the task
        "{thread_name}Task",      // Name of the task
        512,                      // Stack size (in words, not bytes)
        NULL,                     // Task input parameter
        1,                        // Priority of the task
        &Task{thread_name}        // Task handle
    );
'''
    for comm_thread in comm_threads:
        thread_name = f'publishDependum_{process_name(comm_thread.get("name"))}'
        setup_tasks += f'''\
    xTaskCreate(
        {thread_name}Task,        // Function to implement the task
        "{thread_name}Task",      // Name of the task
        512,                      // Stack size (in words, not bytes)
        NULL,                     // Task input parameter
        1,                        // Priority of the task
        &Task{thread_name}        // Task handle
    );
'''
    for listener_thread in listener_threads:
        thread_name = f'receiveDependum_{process_name(listener_thread.get("name"))}'
        setup_tasks += f'''\
    xTaskCreate(
        {thread_name}Task,        // Function to implement the task
        "{thread_name}Task",      // Name of the task
        512,                      // Stack size (in words, not bytes)
        NULL,                     // Task input parameter
        1,                        // Priority of the task
        &Task{thread_name}        // Task handle
    );
'''
    return setup_tasks

def generate_thread_dependencies(thread, cpc):
    """
    Generate the dependency logic for a thread's goal achievement based on its relations.
    """
    thread_id = thread.get("id")
    thread_name = process_name(thread.get("name"))
    if(debug):
        print("Thread ID: ",thread_id)
        print("Thread Name: ",thread_name)

    # Find relations with this thread as the target
    relations = [
        rel for rel in cpc.findall("relation") if rel.get("target") == thread_id
    ]

    # If there are no dependencies, use a default toggle mechanism
    if not relations:
        return f"{thread_name}_GoalAchieved = !{thread_name}_GoalAchieved; // Toggle state for simulation"

    # Extract the operator from the relations
    operator = relations[0].get("operator", "OR").strip().upper()

    print("Operator: ",operator)

    # Build the dependency logic
    dependency_expressions = []
    # Keep accumulating all parameter initializations
    param_initialization = []  # Move this outside the loop if it isn't already there
    for rel in relations:
        source_id = rel.get("source")
        # Check if the source is a thread
        source_thread = next((t for t in cpc.findall("thread") if t.get("id") == source_id), None)
        if source_thread is not None:
            source_thread_name = process_name(source_thread.get("name"))
            dependency_expressions.append(f"{source_thread_name}_GoalAchieved")
        else:
            # Check if the source is a function
            source_function = next((f for f in cpc.findall("function") if f.get("id") == source_id), None)
            function_name = process_name(source_function.get("name"))

            # Extract and accumulate input parameter initializations
            input_parameters = json.loads(source_function.get("input_parameters", "[]"))
            for param in input_parameters:
                param_type = param['type']
                param_name = process_name(param['name'])
                
                # Fetch the Arduino type and default value
                type_info = type_mapping.get(param_type, {"arduino_type": param_type, "default_value": ""})
                arduino_type = type_info["arduino_type"]
                default_value = f" = {type_info['default_value']}" if type_info["default_value"] else ""
                
                # Create the initialization line
                initialization = f"{arduino_type} {param_name}{default_value};"
                if initialization not in param_initialization:  # Avoid duplicates
                    param_initialization.append(initialization)


            # Prepare the function call
            param_call = ", ".join(
                f"{process_name(param['name'])}" for param in input_parameters
            )
            dependency_expressions.append(f"{function_name}({param_call})")
            # Add parameter initialization comments if needed

    param_initialization_str = "\n        ".join(param_initialization)
    if(debug):
        print("Param initialization string: ",param_initialization_str)

    # Join expressions based on the operator
    logical_operator = " || " if operator == "OR" else " && "
    dependency_logic = f"{logical_operator.join(dependency_expressions)}"

    # Final goal achievement assignment
    return f"{param_initialization_str}\n        {thread_name}_GoalAchieved = ({dependency_logic});"

def generate_thread_functions(threads, cpc):
    """
    Generate FreeRTOS task functions for each thread, incorporating dependency logic.
    """
    thread_code = ""
    for thread in threads:
        thread_id = thread.get("id")
        thread_id_cim_parent = thread.get("id_cim_parent")
        thread_name = process_name(thread.get("name"))
        thread_interval_in_milliseconds = thread.get("interval_in_milliseconds")

        qualification_array = thread.get("qualification_array")
        contribution_array = thread.get("contribution_array")
        qualification_comment = ""
        if qualification_array.replace("[]",""):
            qualifications = qualification_array.split(";")
            qualification_comment = "\n".join(
                f" * - \"{qual.strip()}\"" for qual in qualifications
            )
        else:
            qualification_comment = " * None specified."
        # Prepare the contribution array comment (if present)
        contribution_comment = ""
        if contribution_array.replace("[]",""):
            contributions = contribution_array.split(";")
            contribution_comment = "\n".join(
                f" * - \"{contrib.strip()}\"" for contrib in contributions
            )
        else:
            contribution_comment = " * None specified."

        # Generate dependency logic for the thread
        dependency_logic = generate_thread_dependencies(thread, cpc)

        operation_modes_switch = generate_operation_mode_switch(thread, "        ")

        thread_code += f'''
// Task for {thread_name}
void {thread_name}Task(void *pvParameters) {{
    // This variable handles the period in milliseconds for thread execution
    const TickType_t xDelay = pdMS_TO_TICKS({thread_interval_in_milliseconds}); // Example interval for {thread_name}

    // --- {thread_name} Context Information ---
    // ID: {thread_id}
    // ID CIM Parent: {thread_id_cim_parent}
    // qualification_array: 
    // {qualification_comment}
    // contribution_array: 
    // {contribution_comment}
    // ----------------------------------------------------------

    for (;;) {{
        // --- Your code goes here ---
        // Evaluate the state of {thread_name}

        {dependency_logic}
        {operation_modes_switch}
        // --- Your code ends here ---

        vTaskDelay(xDelay);
    }}
}}
'''
    return thread_code

def generate_connectivity_variables(cpc):
    comm_variables_code = ""
    listener_threads = cpc.findall("listenerThread")
    cpc_id = cpc.get("id")
    cpc_name = cpc.get("name")

    for listener_thread in listener_threads:
        listener_thread_name = listener_thread.get("name")
        comm_variables_code += f'const char* {process_name(listener_thread_name)}ClientId = "{process_name(cpc_name)}Client_{process_name(cpc_id)}";\n'
        comm_variables_code += f"WiFiClient {process_name(listener_thread_name)}Client;\n"
        comm_variables_code += f"PubSubClient {process_name(listener_thread_name)}MqttClient({process_name(listener_thread_name)}Client);\n"
    comm_threads = cpc.findall("commThread")
    for comm_thread in comm_threads:
        comm_thread_name = comm_thread.get("name")
        comm_variables_code += f'const char* {process_name(comm_thread_name)}ClientId = "{process_name(cpc_name)}Client_{process_name(cpc_id)}";\n'
        comm_variables_code += f"WiFiClient {process_name(comm_thread_name)}Client;\n"
        comm_variables_code += f"PubSubClient {process_name(comm_thread_name)}MqttClient({process_name(comm_thread_name)}Client);\n"
    return comm_variables_code

def generate_callback_functions(cpc):
    callback_functions_code = ""
    listener_threads = cpc.findall("listenerThread")
    for listener_thread in listener_threads:
        listener_name = process_name(listener_thread.get("name"))
        data_extraction = apply_indentation_to_text(generate_data_extraction(listener_thread), "        ")
        operation_modes = generate_operation_mode_switch(listener_thread, indentation="        ")
        debug_structure = apply_indentation_to_text(generate_debug_listener_print(listener_thread), "                    ")
        client = f"{listener_name}MqttClient"
        callback_functions_code += f'''
void callback_{listener_name}(char* topic, byte* payload, unsigned int length) {{
    Serial.print("Message on Topic 1: ");
    Serial.print(topic);
    Serial.println(" - ");
    // Parse the incoming JSON message
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, payload);

    if (!error) {{
{data_extraction}

        // Debug output to Serial
        Serial.println("Dependum data received:");
        if (debug) {{
{debug_structure}
        }}
    }} else {{
        Serial.println("Error parsing JSON message");
    }}
    // Your custom code to process the dependum can go here
{operation_modes}


}}

'''
    return callback_functions_code

def generate_cpc_ino(cpc, directory):
    """
    Generate the .ino file for the given CPC, including all associated <function> and <thread> objects.
    """
    cpc_id = cpc.get("id")
    cpc_name = cpc.get("name")
    cpc_description = cpc.get("description")
    cpc_parent = cpc.get("id_cim_parent")
    
    comm_mqtt_ids = generate_all_comm_mqtt_ids(cpc)

    connectivity_variables = generate_connectivity_variables(cpc)


    # Include necessary libraries
    ino_content = f'''\
// CPC ID: {cpc_id}
// Parent ID: {cpc_parent}
// Name: {cpc_name}
// Description: {cpc_description}

#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <FreeRTOS_SAMD21.h>
#include <task.h>
#include "secrets.h"
#include "comm_utils.h"
#include <Arduino_JSON.h>
#include <ArduinoJson.h>

// Global variables for WiFi and MQTT connectivity
{connectivity_variables}
bool debug = true;

// MQTT topics for this CPC ({{CPS_id}}/{{CPC_id}}/{{comm_thread_id}})

{comm_mqtt_ids}

// Thread Status variables
'''
    
    # Generate global variables and task handles for each thread
    threads = cpc.findall("thread")
    listner_threads = cpc.findall("listenerThread")
    comm_threads = cpc.findall("commThread")
    thread_definitions = generate_thread_definitions(threads)
    ino_content += thread_definitions

    # Generate Global variables for functions
    ino_content += '''// Function output variables
'''

    functions = cpc.findall("function")
    function_definitions = []
    for function in functions:
        # Parse the output parameters
        output_parameters = json.loads(function.get("output_parameters"))  # Default to an empty list if None
        
        # Process function name
        function_name = process_name(function.get("name"))
        
        # Generate variables with processed function name
        generateVariables(output_parameters, function_name, function_definitions, "", "init")

    ino_content += "".join(function_definitions)

    # Declare all operation mode variables
    operation_mode_declarations = declare_operation_mode_variables(cpc)

    # Include the declarations in the global variables section of the generated code
    ino_content += f"""
// Global Operation Mode Variables
{operation_mode_declarations}
"""
    generated_structs = generate_all_data_structures(cpc, "declare")
    

    ino_content += f'''
// Global Data Structures (software resources and/or any dependum)
{generated_structs}
'''
    comm_handles = generate_comm_thread_handles(cpc)
    if(comm_handles):
        ino_content += f'''
// Comm Thread Handles
{comm_handles}
'''
    listener_handles = generate_listener_thread_handles(cpc)
    if(listener_handles):
        ino_content += f'''
// Listener Thread Handles
{listener_handles}
'''
    setup_task_creation = generate_setup_task_creation(threads, comm_threads, listner_threads)
    if(debug):
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
        print("Setup Task Creation for ",cpc.get("name"),": \n",setup_task_creation)
        print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&")

    ino_content += '''
void setup() {
    if (debug) {
        Serial.begin(9600);
        while (!Serial);
    }
    connectToWiFi();
'''
    setup_connection = apply_indentation_to_text(generate_connection_to_topics(cpc), "    ")
    ino_content += f'''
{setup_connection}
    
    // Create tasks for the operational goals
'''
    ino_content += setup_task_creation + '''
    // Start the threads
    vTaskStartScheduler();
}\n'''
    callback_functions = generate_callback_functions(cpc)
    if(callback_functions):
        ino_content += f'''
{callback_functions}
'''
    
    setup_communication_threads = generate_comm_threads(cpc)
    setup_communication_threads += generate_listener_threads(cpc)
    if(debug):
        print("Setup Communication threads: ", setup_communication_threads)
    if(setup_communication_threads):
        ino_content += f'''
{setup_communication_threads}
'''
    listener_thread_code = generate_listener_thread_code(cpc)
    # Generate the main loop function
    ino_content += f'''
{listener_thread_code}
void loop() {{

    // Let FreeRTOS manage tasks, nothing to do here
    delay(100);
}}
'''

    # Append generated functions for each <function> object after the loop function
    functions = cpc.findall("function")
    for function in functions:
        function_code = generate_function_code(function, cpc)
        ino_content += function_code

    # Generate thread (task) functions with dependencies
    thread_functions = generate_thread_functions(threads, cpc)
    ino_content += thread_functions

    # Write the updated content to the .ino file
    write_to_file(directory, process_name(cpc_name), ino_content, ".ino")




def process_cpcs(xml_file):
    """
    Parse the XML file and generate files for each CPC.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()

    for cpc in root.findall("cpc"):
        cpc_name = cpc.get("name")
        directory = os.path.join("output", cpc_name)
        os.makedirs(directory, exist_ok=True)

        generate_cpc_ino(cpc, directory)
        generate_secrets_file(directory)
        generate_comm_utils_file(directory)

# Example usage (Only for debug)
# Test path: "../input/xml/PIMmidPSM.xml"
xml_file_path = str(sys.argv[1])
tree = ET.parse(xml_file_path)
root = tree.getroot()
root_ids = []
root_ids.append(process_name(root.get("id")))
root_ids.append(process_name(root.get("name")))
CPS_id = "_".join(root_ids)
if(debug):
    print("CPS ID: ",CPS_id)

process_cpcs(xml_file_path)

