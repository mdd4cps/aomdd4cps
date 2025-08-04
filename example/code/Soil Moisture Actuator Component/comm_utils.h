#include <WiFiNINA.h>
#include <PubSubClient.h>
#include "secrets.h"

// Connect to the WiFi network
void connectToWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(SECRET_SSID, SECRET_PASS);

  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(1000);
  }

  Serial.println("Connected to WiFi!");
}

// Set up MQTT connection
void mqttSetup(PubSubClient &client, MQTT_CALLBACK_SIGNATURE) {
  client.setServer(SECRET_MQTT_BROKER, SECRET_MQTT_PORT);
  client.setCallback(callback);
}

// Connect to MQTT Broker and subscribe to a topic
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

// Example MQTT callback (update for your needs)
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived on topic: ");
  Serial.println(topic);
  // Handle payload (optional)
}
