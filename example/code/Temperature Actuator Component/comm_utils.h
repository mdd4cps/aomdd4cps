#include <WiFiNINA.h>
#include <ArduinoMqttClient.h>
#include "secrets.h"



// Global variables for WiFi and MQTT connectivity
extern WiFiClient wifiClient;
extern MqttClient mqttClient;

// Function to connect to the WiFi network
void connectToWiFi(bool debug) {
    if (debug) {
        Serial.print("Connecting to WiFi");
    }

    while (WiFi.status() != WL_CONNECTED) {
        WiFi.begin(SECRET_SSID, SECRET_PASS);
        delay(2000);
        if (debug) {
            Serial.print(".");
        }
    }
    if (debug) {
        Serial.println("\nConnected to WiFi!");
    }
}

// Function to connect to the MQTT broker
void connectToMQTT(const char* mqttTopic, bool debug) {
    while (!mqttClient.connected()) {
        if (debug) {
            Serial.print("Connecting to MQTT...");
        }
        if (mqttClient.connect(SECRET_MQTT_BROKER, SECRET_MQTT_PORT)) {
            if (debug) {
                Serial.println("connected!");
            }
            mqttClient.subscribe(mqttTopic);
        } else {
            if (debug) {
                Serial.print("failed, error code: ");
                Serial.println(mqttClient.connectError());
                Serial.println("Retrying in 5 seconds...");
            }
            delay(5000);
        }
    }
}
