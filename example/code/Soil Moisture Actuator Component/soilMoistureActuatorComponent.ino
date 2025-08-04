// CPC ID: tc0aXw5la06j1g5yClUv-2
// Parent ID: tc0aXw5la06j1g5yClUv-15
// Name: Soil Moisture Actuator Component
// Description: Involucra un m�dulo que utiliza un actuador de v�lvula controlada por un servo motor y cuya l�gica de control depende del valor de humedad monitoreado  por otro nodo de la red y de la especie configurada para la planta.

#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <FreeRTOS_SAMD21.h>
#include <task.h>
#include "secrets.h"
#include "comm_utils.h"
#include <Arduino_JSON.h>
#include <ArduinoJson.h>
#include <Servo.h>

// Global variables for WiFi and MQTT connectivity
const char *soilMoistureData_ListenerThreadClientId = "soilMoistureActuatorComponentClient_tc0axw5la06j1g5ycluv_2";
WiFiClient soilMoistureData_ListenerThreadClient;
PubSubClient soilMoistureData_ListenerThreadMqttClient(soilMoistureData_ListenerThreadClient);

bool debug = true;

// Hardware configuration
int batteryCharge = 100;                                  // Global variable to simulate battery charge (starts at 100%)
const int dipSwitchPins[8] = {12, 11, 10, 9, 8, 7, 6, 5}; // DIP switch pins
Servo valveServo;
const int servoPin = 3; // Servo pin

// Define the array of valid keys and corresponding positions for the dip switch
int SoilMoistureValidKeys[] = {0, 1, 2, 3};
double referenceSoilMoistureArray[] = {70.0, 80.0, 100.0, 110.0};
const double DEFAULT_SOIL_MOISTURE = 90.0; // Default servo position if key is not found

// MQTT topics for this CPC ({CPS_id}/{CPC_id}/{comm_thread_id})

// Listener Topics(Receiver)
const char *soilMoistureData_ListenerThread_topic = "ehetnx6obnygbtiqlszm_greenhouseMonitoringSystem/cvocu7cyytcjj8tokeac_32/tc0axw5la06j1g5ycluv_50_comm_thread/dependum";

// Thread Status variables
bool maintainSoilMoistureLevels_GoalAchieved = false; // Global variable for thread maintainSoilMoistureLevels(ID: tc0aXw5la06j1g5yClUv-3)
TaskHandle_t TaskmaintainSoilMoistureLevels;
bool optimizeResources_GoalAchieved = false; // Global variable for thread optimizeResources(ID: tc0aXw5la06j1g5yClUv-17)
TaskHandle_t TaskoptimizeResources;

// Function output variables
double analyzeBatteryUsage_energyLevel = 0.0;      // Nivel de energ�a de la bater�a del m�dulo.
double checkSoilMoistureLevels_soilMoisture = 0.0; // Nivel de humedad de la planta correspondiente.

// Global Operation Mode Variables
int maintainSoilMoistureLevels_operation_mode = 0; // Initial operation mode: Bajo consumo

// Global Data Structures (software resources and/or any dependum)
struct soilMoistureData_ListenerThread_data_structure
{
    double soilMoisture; // Nivel de humedad de la planta correspondiente.
} soilMoistureData_ListenerThread_data_structure;

// Listener Thread Handles
TaskHandle_t TaskreceiveDependum_soilMoistureData_ListenerThread;

void setup()
{
    if (debug)
    {
        Serial.begin(9600);
        while (!Serial)
            ;
    }
    connectToWiFi();

    // Listener Topics(Receiver)
    mqttSetup(soilMoistureData_ListenerThreadMqttClient, callbacksoilMoistureData_ListenerThread);
    connectToMQTT(soilMoistureData_ListenerThreadMqttClient, soilMoistureData_ListenerThreadClientId, soilMoistureData_ListenerThread_topic);

    // Create tasks for the operational goals
    xTaskCreate(
        maintainSoilMoistureLevelsTask,   // Function to implement the task
        "maintainSoilMoistureLevelsTask", // Name of the task
        512,                              // Stack size (in words, not bytes)
        NULL,                             // Task input parameter
        1,                                // Priority of the task
        &TaskmaintainSoilMoistureLevels   // Task handle
    );
    xTaskCreate(
        optimizeResourcesTask,   // Function to implement the task
        "optimizeResourcesTask", // Name of the task
        512,                     // Stack size (in words, not bytes)
        NULL,                    // Task input parameter
        1,                       // Priority of the task
        &TaskoptimizeResources   // Task handle
    );
    xTaskCreate(
        receiveDependum_soilMoistureData_ListenerThreadTask,   // Function to implement the task
        "receiveDependum_soilMoistureData_ListenerThreadTask", // Name of the task
        512,                                                   // Stack size (in words, not bytes)
        NULL,                                                  // Task input parameter
        1,                                                     // Priority of the task
        &TaskreceiveDependum_soilMoistureData_ListenerThread   // Task handle
    );

    // Start the threads
    vTaskStartScheduler();
}

void callbacksoilMoistureData_ListenerThread(char *topic, byte *payload, unsigned int length)
{
    Serial.println("Running Callback Function: 'callbacksoilMoistureData_ListenerThread'");
    Serial.print("====Message on Topic 1: ");
    Serial.print(topic);
    Serial.println(" - ");
    // Parse the incoming JSON message
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, payload);

    if (!error)
    {
        soilMoistureData_ListenerThread_data_structure.soilMoisture = doc["soilMoisture"];

        // Debug output to Serial
        Serial.println("====Dependum data received:");
        if (debug)
        {
            Serial.print("====soilMoisture: ");
            Serial.println(soilMoistureData_ListenerThread_data_structure.soilMoisture);
        }
    }
    else
    {
        Serial.println("====Error parsing JSON message");
    }
    // Your custom code to process the dependum can go here
}

void receiveDependum_soilMoistureData_ListenerThreadTask(void *pvParameters)
{

    //
    // --- Listener Thread Information ---
    // Name: Soil Moisture Data - Listener Thread
    // ID: tc0aXw5la06j1g5yClUv-50-listener_thread
    // Description: This Listener Thread is responsible for receiving the dependum: soilMoistureData_ListenerThread_data_structure
    //
    // Original Element in PIM: Soil Moisture Data - Listener Thread
    // Transformed To: Function `soilMoistureData_ListenerThread()`
    //
    // Note for Developers:
    // The `dependum` data should be stored on and then retrieved from the function checkSoilMoistureLevels().
    // Ensure the function completes its operation and receives the required data
    // in the appropriate format for reception.
    //
    // Qualification Array:
    //  * None specified.
    //
    // Contribution Array:
    //  * None specified.
    //
    //
    // This variable handles the period in milliseconds for thread execution
    const TickType_t xDelay = pdMS_TO_TICKS(10000);

    Serial.println("Running Thread: 'receiveDependum_soilMoistureData_ListenerThreadTask'");
    for (;;)
    {

        // Check MQTT connection status
        if (!soilMoistureData_ListenerThreadMqttClient.connected())
        {
            connectToMQTT(soilMoistureData_ListenerThreadMqttClient, soilMoistureData_ListenerThreadClientId, soilMoistureData_ListenerThread_topic);
        }

        // Always poll MQTT for new messages
        Serial.println("====Polling messages...");
        soilMoistureData_ListenerThreadMqttClient.loop();

        // Keep delay to avoid overloading loop but keep polling
        vTaskDelay(xDelay);
    }
}

void loop()
{

    // Let FreeRTOS manage tasks, nothing to do here
    delay(100);
}

bool changeSoilMoisture(double soilMoistureReferenceValue, int changeSoilMoisture_operation_mode = 0)
{
    // Function ID: tc0aXw5la06j1g5yClUv-4
    // Parent ID: tc0aXw5la06j1g5yClUv-4
    // Input Parameters:
    // Soil Moisture Reference Value(double) - Nivel de humedad al cual se deber�a llegar.
    // Output Parameters:
    // Qualification Array:
    //  * None specified.
    // Contribution Array:
    //  * - "[{ "softgoal_id": "tc0aXw5la06j1g5yClUv-5", "name": "Resource Efficiency", "contribution": "hurt"}]"
    // Hardware Resource Assigned:
    // Plant Waterer:
    //     ID: tc0aXw5la06j1g5yClUv-20
    //     Parent ID: tc0aXw5la06j1g5yClUv-20
    //     Description: Este dispositivo corresponde a una v�lvula de agua controlada por un servo  motor e 180 grados, para lo cual se debe incluir la librer�a correspondiente(servo.h).
    // Plant Configuration Pin:
    //     ID: U5gbfCX47OS8Pz70eV5W-3
    //     Parent ID: U5gbfCX47OS8Pz70eV5W-3
    //     Description: Se utilizar� un pin digital para seleccionar la especie en cultivo. 0 es  para tomate, y 1 para lechuga. Se debe implementar el conexionado  mediante dip switch para la selecci�n.
    // Set output parameters
    Serial.println("===>Running Function 'analyzeBatteryUsage'");

    // --- Your code goes here ---
    Serial.print("========Reference Soil Moisture = ");
    Serial.println(soilMoistureReferenceValue);
    Serial.print("========Current Soil Moisture= ");
    Serial.println(checkSoilMoistureLevels_soilMoisture);

    switch (changeSoilMoisture_operation_mode)
    {
    case 0: // Bajo consumo - Dependiendo de la planta configurada, se va accionar el  riego cuando el nivel de humedad se encuentre a un 20% inferior al nivel  promedio establecido para la especie, llegando al nivel promedio de  humedad.
        if (checkSoilMoistureLevels_soilMoisture < (soilMoistureReferenceValue * 0.8))
        {
            Serial.println("========Activating Watering Valve...");
            valveServo.write(180);
        }
        else
        {
            Serial.println("========Optimal Soil Moisture, no watering required.");
            valveServo.write(0);
        }
        break;
    case 1: // Alto Consumo - Dependiendo de la planta configurada, se va accionar el  riego cuando el nivel de humedad se encuentre a un 10% inferior al nivel  promdio establecido para la especie, de manera que se llegue al  promedio del rango �ptimo de humedad.
        if (checkSoilMoistureLevels_soilMoisture < (soilMoistureReferenceValue * 0.9))
        {
            Serial.println("========Activating Watering Valve...");
            valveServo.write(180);
        }
        else
        {
            Serial.println("========Optimal Soil Moisture, no watering required.");
            valveServo.write(0);
        }
        break;
    default:
        // Handle undefined operation modes
        break;
    }

    return true;

    // --- Your code goes here ---
}

bool analyzeBatteryUsage()
{
    // Function ID: tc0aXw5la06j1g5yClUv-7
    // Parent ID: tc0aXw5la06j1g5yClUv-7
    // Input Parameters:
    // Output Parameters:
    // Energy Level(double) - Nivel de energ�a de la bater�a del m�dulo.
    // Qualification Array:
    //  * None specified.
    // Contribution Array:
    //  * None specified.
    // Hardware Resource Assigned:
    // Set output parameters
    Serial.println("===>Running Function 'analyzeBatteryUsage'");
    analyzeBatteryUsage_energyLevel = getBatteryCharge(); // Nivel de energ�a de la bater�a del m�dulo.
    Serial.print("========Battery charge: ");
    Serial.println(analyzeBatteryUsage_energyLevel);

    // --- Your code goes here ---

    return true;

    // --- Your code goes here ---
}

bool checkSoilMoistureLevels()
{
    // Function ID: tc0aXw5la06j1g5yClUv-9
    // Parent ID: tc0aXw5la06j1g5yClUv-9
    // Input Parameters:
    // Output Parameters:
    // Soil Moisture(double) - Nivel de humedad de la planta correspondiente.
    // Qualification Array:
    //  * None specified.
    // Contribution Array:
    //  * None specified.
    // Hardware Resource Assigned:
    // Set output parameters
    Serial.println("===>Running Function 'checkSoilMoistureLevels'");
    checkSoilMoistureLevels_soilMoisture = soilMoistureData_ListenerThread_data_structure.soilMoisture; // Nivel de humedad de la planta correspondiente.
    Serial.print("========Current Moisture Levels: ");
    Serial.println(checkSoilMoistureLevels_soilMoisture);
    // --- Your code goes here ---

    return true;

    // --- Your code goes here ---
}

bool changeEnergyMode(double energyLevel)
{
    // Function ID: tc0aXw5la06j1g5yClUv-6
    // Parent ID: tc0aXw5la06j1g5yClUv-6
    // Input Parameters:
    // Energy Level(double) - Nivel de energ�a de la bater�a del m�dulo.
    // Output Parameters:
    // Qualification Array:
    //  * None specified.
    // Contribution Array:
    //  * None specified.
    // Hardware Resource Assigned:
    // Set output parameters
    Serial.println("===>Running Function 'changeEnergyMode'");

    // --- Your code goes here ---

    if (energyLevel < 50)
    {
        maintainSoilMoistureLevels_operation_mode = 0;
    }
    else
    {
        maintainSoilMoistureLevels_operation_mode = 1;
    }

    Serial.print("========Energy Mode: ");
    Serial.println(maintainSoilMoistureLevels_operation_mode);
    return true;

    // --- Your code goes here ---
}

// Task for maintainSoilMoistureLevels
void maintainSoilMoistureLevelsTask(void *pvParameters)
{
    // This variable handles the period in milliseconds for thread execution
    const TickType_t xDelay = pdMS_TO_TICKS(10000); // Example interval for maintainSoilMoistureLevels

    // --- maintainSoilMoistureLevels Context Information ---
    // ID: tc0aXw5la06j1g5yClUv-3
    // ID CIM Parent: tc0aXw5la06j1g5yClUv-3
    // qualification_array:
    //  * None specified.
    // contribution_array:
    //  * None specified.
    // ----------------------------------------------------------

    for (;;)
    {
        // --- Your code goes here ---
        // Evaluate the state of maintainSoilMoistureLevels

        Serial.println("Running Thread 'maintainSoilMoistureLevelsTask'");
        double soilMoistureReferenceValue = DEFAULT_SOIL_MOISTURE;
        int dipValue = readDipSwitches();
        Serial.print("====Dip Switch Value: ");
        Serial.println(dipValue);
        for (int i = 0; i < sizeof(SoilMoistureValidKeys) / sizeof(SoilMoistureValidKeys[0]); i++)
        {
            if (dipValue == SoilMoistureValidKeys[i])
            {
                soilMoistureReferenceValue = referenceSoilMoistureArray[i];
                break;
            }
        }
        Serial.println("====Operation mode: " + maintainSoilMoistureLevels_operation_mode);
        switch (maintainSoilMoistureLevels_operation_mode)
        {
        case 0: // Bajo consumo - Dependiendo de la planta configurada, se va accionar el  riego cuando el nivel de humedad se encuentre a un 20% inferior al nivel  promedio establecido para la especie, llegando al nivel promedio de  humedad.
            maintainSoilMoistureLevels_GoalAchieved = (checkSoilMoistureLevels() && changeSoilMoisture(soilMoistureReferenceValue, 0));
            break;
        case 1: // Alto Consumo - Dependiendo de la planta configurada, se va accionar el  riego cuando el nivel de humedad se encuentre a un 10% inferior al nivel  promdio establecido para la especie, de manera que se llegue al  promedio del rango �ptimo de humedad.
            maintainSoilMoistureLevels_GoalAchieved = (checkSoilMoistureLevels() && changeSoilMoisture(soilMoistureReferenceValue, 1));
            break;
        default:
            // Handle undefined operation modes
            break;
        }

        // --- Your code ends here ---

        vTaskDelay(xDelay);
    }
}

// Task for optimizeResources
void optimizeResourcesTask(void *pvParameters)
{
    // This variable handles the period in milliseconds for thread execution
    const TickType_t xDelay = pdMS_TO_TICKS(10000); // Example interval for optimizeResources

    // --- optimizeResources Context Information ---
    // ID: tc0aXw5la06j1g5yClUv-17
    // ID CIM Parent: tc0aXw5la06j1g5yClUv-17
    // qualification_array:
    //  * None specified.
    // contribution_array:
    //  * - "[{ "softgoal_id": "tc0aXw5la06j1g5yClUv-5", "name": "Resource Efficiency", "contribution": "help"}]"
    // ----------------------------------------------------------

    Serial.println("Running Thread 'optimizeResourcesTask'");
    for (;;)
    {
        // --- Your code goes here ---
        // Evaluate the state of optimizeResources

        double energyLevel = analyzeBatteryUsage_energyLevel;
        Serial.print("======== Energy Level: ");
        Serial.println(energyLevel);
        optimizeResources_GoalAchieved = (analyzeBatteryUsage() && changeEnergyMode(energyLevel));

        // --- Your code ends here ---

        vTaskDelay(xDelay);
    }
}

// Function to read DIP switch states and return an 8-bit value
int readDipSwitches()
{
    int value = 0;

    for (int i = 0; i < 8; i++)
    {
        value |= (!digitalRead(dipSwitchPins[i])) << i; // Read pins and build the value
    }

    return value;
}

int getBatteryCharge()
{
    // Decrease charge by 1%
    batteryCharge = batteryCharge - 10;

    // Reset to 100% if charge reaches 0%
    if (batteryCharge < 0)
    {
        batteryCharge = 100;
    }

    return batteryCharge;
}
