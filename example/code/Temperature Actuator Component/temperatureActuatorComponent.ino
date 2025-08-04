// CPC ID: tc0aXw5la06j1g5yClUv-24
// Parent ID: tc0aXw5la06j1g5yClUv-37
// Name: Temperature Actuator Component
// Description: Involucra un m�dulo que utiliza un actuador de calefactor para el  invernadero(accionado a trav�s de una se�al digital) y cuya l�gica de  control depende del valor de temperatura del invernadero monitoreado por otro nodo de la red.

#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <FreeRTOS_SAMD21.h>
#include <task.h>
#include "secrets.h"
#include "comm_utils.h"
#include <Arduino_JSON.h>
#include <ArduinoJson.h>

// Global variables for WiFi and MQTT connectivity
const char *temperatureData_ListenerThreadClientId = "temperatureActuatorComponentClient_tc0axw5la06j1g5ycluv_24";
WiFiClient temperatureData_ListenerThreadClient;
PubSubClient temperatureData_ListenerThreadMqttClient(temperatureData_ListenerThreadClient);

bool debug = true;
int batteryCharge = 100; // Global variable to simulate battery charge (starts at 100%)

// Constants
#define HEATERON_PIN 0
#define HEATEROFF_PIN 1
#define MAX_TEMP 30
#define MIN_TEMP 23

// MQTT topics for this CPC ({CPS_id}/{CPC_id}/{comm_thread_id})

// Listener Topics(Receiver)
const char *temperatureData_ListenerThread_topic = "ehetnx6obnygbtiqlszm_greenhouseMonitoringSystem/cvocu7cyytcjj8tokeac_5/tc0axw5la06j1g5ycluv_51_comm_thread/dependum";

// Thread Status variables
bool maintainGreenhouseTemperature_GoalAchieved = false; // Global variable for thread maintainGreenhouseTemperature(ID: tc0aXw5la06j1g5yClUv-25)
TaskHandle_t TaskmaintainGreenhouseTemperature;
bool optimizeResources_GoalAchieved = false; // Global variable for thread optimizeResources(ID: tc0aXw5la06j1g5yClUv-39)
TaskHandle_t TaskoptimizeResources;

// Function output variables
double checkGreenhouseTemperature_greenhouseTemp = 0.0; // Temperatura ambiental del invernadero.
double analyzeBatteryUsage_energyLevel = 0.0;           // Nivel de energ�a de la bater�a del m�dulo.

// Global Operation Mode Variables
int maintainGreenhouseTemperature_operation_mode = 0; // Initial operation mode: Bajo consumo

// Global Data Structures (software resources and/or any dependum)
struct temperatureData_ListenerThread_data_structure
{
    double greenhouseTemp; // Temperatura ambiental del invernadero.
} temperatureData_ListenerThread_data_structure;

// Listener Thread Handles
TaskHandle_t TaskreceiveDependum_temperatureData_ListenerThread;

void setup()
{
    if (debug)
    {
        Serial.begin(9600);
        while (!Serial)
            ;
    }

    // Inititialize Heater LEDs
    pinMode(HEATERON_PIN, OUTPUT);
    pinMode(HEATEROFF_PIN, OUTPUT);

    // The heater starts OFF
    digitalWrite(HEATEROFF_PIN, HIGH);

    connectToWiFi();

    // Listener Topics(Receiver)
    mqttSetup(temperatureData_ListenerThreadMqttClient, callback_temperatureData_ListenerThread);
    connectToMQTT(temperatureData_ListenerThreadMqttClient, temperatureData_ListenerThreadClientId, temperatureData_ListenerThread_topic);

    // Create tasks for the operational goals
    xTaskCreate(
        maintainGreenhouseTemperatureTask,   // Function to implement the task
        "maintainGreenhouseTemperatureTask", // Name of the task
        512,                                 // Stack size (in words, not bytes)
        NULL,                                // Task input parameter
        1,                                   // Priority of the task
        &TaskmaintainGreenhouseTemperature   // Task handle
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
        receiveDependum_temperatureData_ListenerThreadTask,   // Function to implement the task
        "receiveDependum_temperatureData_ListenerThreadTask", // Name of the task
        512,                                                  // Stack size (in words, not bytes)
        NULL,                                                 // Task input parameter
        1,                                                    // Priority of the task
        &TaskreceiveDependum_temperatureData_ListenerThread   // Task handle
    );

    // Start the threads
    vTaskStartScheduler();
}

void activateHeater(int delayMilliseconds = 5000)
{
    digitalWrite(HEATEROFF_PIN, LOW);
    digitalWrite(HEATERON_PIN, HIGH);
    Serial.print("========Heater ON... for ");
    Serial.print(delayMilliseconds);
    Serial.println(" milliseconds.");
    delay(delayMilliseconds);
    digitalWrite(HEATERON_PIN, LOW);
    digitalWrite(HEATEROFF_PIN, HIGH);
}

void callback_temperatureData_ListenerThread(char *topic, byte *payload, unsigned int length)
{
    Serial.println("====Running Callback 'callback_temperatureData_ListenerThread'");
    Serial.print("========Message on Topic: ");
    Serial.print(topic);
    Serial.println(" - ");
    // Parse the incoming JSON message
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, payload);

    if (!error)
    {
        temperatureData_ListenerThread_data_structure.greenhouseTemp = doc["greenhouseTemp"];

        // Debug output to Serial
        Serial.println("========Dependum Data Received:");
        if (debug)
        {
            Serial.print("========greenhouseTemp: ");
            Serial.println(temperatureData_ListenerThread_data_structure.greenhouseTemp);
        }
    }
    else
    {
        Serial.println("========Error parsing JSON message");
    }
    // Your custom code to process the dependum can go here
}

void receiveDependum_temperatureData_ListenerThreadTask(void *pvParameters)
{

    //
    // --- Listener Thread Information ---
    // Name: Temperature Data - Listener Thread
    // ID: tc0aXw5la06j1g5yClUv-51-listener_thread
    // Description: This Listener Thread is responsible for receiving the dependum: temperatureData_ListenerThread_data_structure
    //
    // Original Element in PIM: Temperature Data - Listener Thread
    // Transformed To: Function `temperatureData_ListenerThread()`
    //
    // Note for Developers:
    // The `dependum` data should be stored on and then retrieved from the function checkGreenhouseTemperature().
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
    Serial.println("Running Thread 'receiveDependum_temperatureData_ListenerThreadTask'");
    const TickType_t xDelay = pdMS_TO_TICKS(10000);

    for (;;)
    {

        // Check MQTT connection status
        if (!temperatureData_ListenerThreadMqttClient.connected())
        {
            connectToMQTT(temperatureData_ListenerThreadMqttClient, temperatureData_ListenerThreadClientId, temperatureData_ListenerThread_topic);
        }

        // Always poll MQTT for new messages
        Serial.println("(polling)");
        temperatureData_ListenerThreadMqttClient.loop();

        // Keep delay to avoid overloading loop but keep polling
        vTaskDelay(xDelay);
    }
}

void loop()
{

    // Let FreeRTOS manage tasks, nothing to do here
    delay(100);
}

bool changeGreenhouseTemperature(double temperatureReferenceValue, int changeGreenhouseTemperature_operation_mode = 0)
{
    // Function ID: tc0aXw5la06j1g5yClUv-26
    // Parent ID: tc0aXw5la06j1g5yClUv-26
    // Input Parameters:
    // Temperature Reference Value(double) - Temperatura a la cual se deber�a llegar.
    // Output Parameters:
    // Qualification Array:
    //  * None specified.
    // Contribution Array:
    //  * - "[{ "softgoal_id": "tc0aXw5la06j1g5yClUv-27", "name": "Resource Efficiency", "contribution": "hurt"}]"
    // Hardware Resource Assigned:
    // Greenhouse Heater:
    //     ID: tc0aXw5la06j1g5yClUv-42
    //     Parent ID: tc0aXw5la06j1g5yClUv-42
    //     Description: Este dispositivo corresponde a un calefactor que es controlado mediante un  rel� via se�al digital desde el CPC. Se debe implementar el conexionado  mediante protoboard.
    // Set output parameters

    Serial.println("===>Running Function 'changeGreenhouseTemperature'");
    // --- Your code goes here ---

    Serial.print("========Reference Temperature = ");
    Serial.println(temperatureReferenceValue);
    Serial.print("========Current Temperature= ");
    Serial.println(checkGreenhouseTemperature_greenhouseTemp);

    switch (changeGreenhouseTemperature_operation_mode)
    {
    case 0: // Bajo consumo - Se va accionar el calefactor cuando la temperatura del  invernadero disminuya un 10% del promedio de temperatura ideal, de  manera que se produzcan menos accionamientos en un periodo dado.
        if (checkGreenhouseTemperature_greenhouseTemp < (temperatureReferenceValue * 0.9))
        {
            Serial.println("========Activating Heater...");
            activateHeater(5000);
        }
        else
        {
            Serial.println("========Optimal temperature, no heating required.");
        }
        break;
    case 1: // Alto Consumo - Se va accionar el calefactor cuando la temperatura del  invernadero disminuya un 1% del promedio de temperatura ideal, de manera  que se produzcan m�s accionamientos en un periodo dado para una  regulaci�n de temperatura m�s precisa y estable.
        if (checkGreenhouseTemperature_greenhouseTemp < (temperatureReferenceValue * 0.99))
        {
            Serial.println("========Activating Heater...");
            activateHeater(5000);
        }
        else
        {
            Serial.println("========Optimal temperature, no heating required.");
        }
        break;
    default:
        // Handle undefined operation modes
        break;
    }

    return true;

    // --- Your code goes here ---
}

bool changeEnergyMode(double energyLevel)
{
    // Function ID: tc0aXw5la06j1g5yClUv-28
    // Parent ID: tc0aXw5la06j1g5yClUv-28
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
        maintainGreenhouseTemperature_operation_mode = 0;
    }
    else
    {
        maintainGreenhouseTemperature_operation_mode = 1;
    }
    Serial.print("========maintainGreenhouseTemperature_operation_mode = ");
    Serial.println(maintainGreenhouseTemperature_operation_mode);

    return true;

    // --- Your code goes here ---
}

bool checkGreenhouseTemperature()
{
    // Function ID: tc0aXw5la06j1g5yClUv-31
    // Parent ID: tc0aXw5la06j1g5yClUv-31
    // Input Parameters:
    // Output Parameters:
    // Greenhouse Temp(double) - Temperatura ambiental del invernadero.
    // Qualification Array:
    //  * None specified.
    // Contribution Array:
    //  * None specified.
    // Hardware Resource Assigned:
    // Set output parameters
    Serial.println("===>Running Function 'checkGreenhouseTemperature'");

    checkGreenhouseTemperature_greenhouseTemp = temperatureData_ListenerThread_data_structure.greenhouseTemp; // Temperatura ambiental del invernadero.

    // --- Your code goes here ---

    Serial.print("========checkGreenhouseTemperature_greenhouseTemp = ");
    Serial.println(checkGreenhouseTemperature_greenhouseTemp);

    return true;

    // --- Your code goes here ---
}

bool analyzeBatteryUsage()
{
    // Function ID: tc0aXw5la06j1g5yClUv-29
    // Parent ID: tc0aXw5la06j1g5yClUv-29
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

// Task for maintainGreenhouseTemperature
void maintainGreenhouseTemperatureTask(void *pvParameters)
{
    // This variable handles the period in milliseconds for thread execution
    const TickType_t xDelay = pdMS_TO_TICKS(10000); // Example interval for maintainGreenhouseTemperature

    // --- maintainGreenhouseTemperature Context Information ---
    // ID: tc0aXw5la06j1g5yClUv-25
    // ID CIM Parent: tc0aXw5la06j1g5yClUv-25
    // qualification_array:
    //  * None specified.
    // contribution_array:
    //  * None specified.
    // ----------------------------------------------------------

    for (;;)
    {
        // --- Your code goes here ---
        // Evaluate the state of maintainGreenhouseTemperature

        Serial.println("Running Thread 'maintainGreenhouseTemperatureTask'");

        double temperatureReferenceValue = (MAX_TEMP + MIN_TEMP) / 2;
        Serial.print("====Temperature Reference value: ");
        Serial.println(temperatureReferenceValue);

        switch (maintainGreenhouseTemperature_operation_mode)
        {
        case 0: // Bajo consumo - Se va accionar el calefactor cuando la temperatura del  invernadero disminuya un 10% del promedio de temperatura ideal, de  manera que se produzcan menos accionamientos en un periodo dado.
            maintainGreenhouseTemperature_GoalAchieved = (checkGreenhouseTemperature() && changeGreenhouseTemperature(temperatureReferenceValue, 0));
            break;
        case 1: // Alto Consumo - Se va accionar el calefactor cuando la temperatura del  invernadero disminuya un 1% del promedio de temperatura ideal, de manera  que se produzcan m�s accionamientos en un periodo dado para una  regulaci�n de temperatura m�s precisa y estable.
            maintainGreenhouseTemperature_GoalAchieved = (checkGreenhouseTemperature() && changeGreenhouseTemperature(temperatureReferenceValue, 1));
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
    // ID: tc0aXw5la06j1g5yClUv-39
    // ID CIM Parent: tc0aXw5la06j1g5yClUv-39
    // qualification_array:
    //  * None specified.
    // contribution_array:
    //  * - "[{ "softgoal_id": "tc0aXw5la06j1g5yClUv-27", "name": "Resource Efficiency", "contribution": "help"}]"
    // ----------------------------------------------------------

    for (;;)
    {
        Serial.println("Running Thread 'optimizeResourcesTask'");
        // --- Your code goes here ---
        // Evaluate the state of optimizeResources

        double energyLevel = analyzeBatteryUsage_energyLevel;
        Serial.print("====Energy Level: ");
        Serial.println(energyLevel);
        optimizeResources_GoalAchieved = (analyzeBatteryUsage() && changeEnergyMode(energyLevel));

        // --- Your code ends here ---

        vTaskDelay(xDelay);
    }
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