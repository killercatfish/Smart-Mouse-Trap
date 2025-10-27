/*
 * ESP32 Gateway Firmware
 * 
 * Features:
 * - Receives ESP-NOW messages from trap nodes
 * - Forwards messages to Raspberry Pi via MQTT
 * - Maintains connection health monitoring
 * - Always-on (USB powered)
 */

#include <WiFi.h>
#include <esp_now.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ==================== CONFIGURATION ====================
// WiFi credentials - CHANGE THESE
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT broker settings
const char* mqtt_server = "raspberrypi.local";  // Or use IP address
const int mqtt_port = 1883;
const char* mqtt_user = "trapmonitor";  // Optional
const char* mqtt_password = "";  // Optional

// MQTT topics
const char* mqtt_topic_prefix = "trap/";
const char* gateway_status_topic = "gateway/status";

// Status LED
#define LED_PIN 2  // Built-in LED on most ESP32 boards

// ==================== DATA STRUCTURES ====================
typedef struct {
  uint8_t node_id;
  uint8_t event_type;  // 0=status, 1=trigger, 2=low_battery
  uint32_t trap_count;
  float battery_voltage;
  uint8_t route_hops;
  uint32_t timestamp;
} TrapMessage;

// ==================== GLOBAL OBJECTS ====================
WiFiClient espClient;
PubSubClient mqttClient(espClient);

unsigned long lastStatusUpdate = 0;
const unsigned long STATUS_INTERVAL = 60000;  // Send gateway status every 60 seconds

uint32_t messagesReceived = 0;
uint32_t messagesForwarded = 0;

// ==================== WIFI CONNECTION ====================
void setupWiFi() {
  Serial.println("\n=== Connecting to WiFi ===");
  Serial.print("SSID: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_AP_STA);  // Both AP and STA mode for ESP-NOW + WiFi
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));  // Blink while connecting
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("MAC Address: ");
    Serial.println(WiFi.macAddress());
    digitalWrite(LED_PIN, HIGH);
  } else {
    Serial.println("\nWiFi connection failed!");
    digitalWrite(LED_PIN, LOW);
  }
}

// ==================== MQTT CONNECTION ====================
void reconnectMQTT() {
  int attempts = 0;
  
  while (!mqttClient.connected() && attempts < 5) {
    Serial.print("Attempting MQTT connection...");
    
    String clientId = "ESP32Gateway-";
    clientId += String(random(0xffff), HEX);
    
    if (mqttClient.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("connected");
      
      // Publish gateway online status
      mqttClient.publish(gateway_status_topic, "{\"status\":\"online\"}");
      
      digitalWrite(LED_PIN, HIGH);
      return;
    } else {
      Serial.print("failed, rc=");
      Serial.print(mqttClient.state());
      Serial.println(" retrying in 5 seconds");
      
      digitalWrite(LED_PIN, LOW);
      delay(5000);
      attempts++;
    }
  }
}

// ==================== ESP-NOW CALLBACK ====================
void onDataReceive(const uint8_t *mac, const uint8_t *data, int len) {
  Serial.println("\n=== ESP-NOW Message Received ===");
  
  // Blink LED to indicate message reception
  digitalWrite(LED_PIN, LOW);
  delay(50);
  digitalWrite(LED_PIN, HIGH);
  
  messagesReceived++;
  
  // Parse the incoming message
  if (len != sizeof(TrapMessage)) {
    Serial.println("Invalid message size");
    return;
  }
  
  TrapMessage msg;
  memcpy(&msg, data, sizeof(msg));
  
  // Print message details
  Serial.printf("From MAC: %02X:%02X:%02X:%02X:%02X:%02X\n",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  Serial.printf("Node ID: %d\n", msg.node_id);
  Serial.printf("Event Type: %d ", msg.event_type);
  
  switch(msg.event_type) {
    case 0:
      Serial.println("(Status Update)");
      break;
    case 1:
      Serial.println("(TRAP TRIGGERED!)");
      break;
    case 2:
      Serial.println("(Low Battery Warning)");
      break;
    default:
      Serial.println("(Unknown)");
  }
  
  Serial.printf("Trap Count: %d\n", msg.trap_count);
  Serial.printf("Battery: %.2fV\n", msg.battery_voltage);
  Serial.printf("Hops: %d\n", msg.route_hops);
  Serial.printf("Timestamp: %d ms\n", msg.timestamp);
  
  // Forward to MQTT
  forwardToMQTT(msg, mac);
}

// ==================== MQTT FORWARDING ====================
void forwardToMQTT(const TrapMessage &msg, const uint8_t *mac) {
  // Ensure MQTT is connected
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  
  if (!mqttClient.connected()) {
    Serial.println("Cannot forward - MQTT not connected");
    return;
  }
  
  // Create JSON document
  StaticJsonDocument<256> doc;
  
  doc["node_id"] = msg.node_id;
  doc["event_type"] = msg.event_type;
  doc["trap_count"] = msg.trap_count;
  doc["battery_voltage"] = msg.battery_voltage;
  doc["route_hops"] = msg.route_hops;
  doc["timestamp"] = msg.timestamp;
  doc["gateway_time"] = millis();
  
  // Add MAC address
  char macStr[18];
  snprintf(macStr, sizeof(macStr), "%02X:%02X:%02X:%02X:%02X:%02X",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  doc["mac_address"] = macStr;
  
  // Event type string
  const char* eventTypeStr;
  switch(msg.event_type) {
    case 0: eventTypeStr = "status"; break;
    case 1: eventTypeStr = "trigger"; break;
    case 2: eventTypeStr = "low_battery"; break;
    default: eventTypeStr = "unknown";
  }
  doc["event_type_str"] = eventTypeStr;
  
  // Serialize JSON
  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);
  
  // Create topic based on node ID and event type
  char topic[64];
  snprintf(topic, sizeof(topic), "%s%d/%s", 
           mqtt_topic_prefix, msg.node_id, eventTypeStr);
  
  // Publish to MQTT
  if (mqttClient.publish(topic, jsonBuffer)) {
    Serial.println("Message forwarded to MQTT");
    Serial.print("Topic: ");
    Serial.println(topic);
    Serial.print("Payload: ");
    Serial.println(jsonBuffer);
    messagesForwarded++;
  } else {
    Serial.println("Failed to publish to MQTT");
  }
}

// ==================== STATUS REPORTING ====================
void publishGatewayStatus() {
  if (!mqttClient.connected()) {
    return;
  }
  
  StaticJsonDocument<256> doc;
  doc["status"] = "online";
  doc["uptime"] = millis() / 1000;
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["messages_received"] = messagesReceived;
  doc["messages_forwarded"] = messagesForwarded;
  doc["free_heap"] = ESP.getFreeHeap();
  
  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);
  
  mqttClient.publish(gateway_status_topic, jsonBuffer);
  
  Serial.println("\n=== Gateway Status Update ===");
  Serial.println(jsonBuffer);
}

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\n=== ESP32 Gateway Starting ===");
  
  // Configure LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Setup WiFi
  setupWiFi();
  
  // Setup MQTT
  mqttClient.setServer(mqtt_server, mqtt_port);
  reconnectMQTT();
  
  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed");
    while (1) {
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));
      delay(200);
    }
  }
  
  Serial.println("ESP-NOW initialized");
  
  // Register receive callback
  esp_now_register_recv_cb(onDataReceive);
  
  Serial.println("\n=== Gateway Ready ===");
  Serial.println("Waiting for trap messages...");
  
  // Initial status update
  publishGatewayStatus();
}

// ==================== MAIN LOOP ====================
void loop() {
  // Maintain MQTT connection
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
  
  // Maintain WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected - reconnecting...");
    setupWiFi();
  }
  
  // Periodic status updates
  if (millis() - lastStatusUpdate > STATUS_INTERVAL) {
    publishGatewayStatus();
    lastStatusUpdate = millis();
  }
  
  // Small delay to prevent watchdog issues
  delay(10);
}

// ==================== NOTES ====================
/*
 * SETUP INSTRUCTIONS:
 * 
 * 1. Update WiFi credentials at the top of this file
 * 2. Update MQTT broker address (raspberrypi.local or IP)
 * 3. Flash to ESP32 board (any model with WiFi + BLE)
 * 4. Connect via USB power (always-on operation)
 * 5. Note the MAC address from Serial Monitor
 * 6. Use this MAC in trap node firmware configuration
 * 
 * MQTT MESSAGE FORMAT:
 * Topic: trap/{node_id}/{event_type}
 * Example: trap/1/trigger
 * 
 * Payload (JSON):
 * {
 *   "node_id": 1,
 *   "event_type": 1,
 *   "event_type_str": "trigger",
 *   "trap_count": 5,
 *   "battery_voltage": 3.85,
 *   "route_hops": 0,
 *   "timestamp": 123456,
 *   "gateway_time": 234567,
 *   "mac_address": "AA:BB:CC:DD:EE:FF"
 * }
 * 
 * TROUBLESHOOTING:
 * - LED off: WiFi or MQTT connection issue
 * - LED on solid: Gateway ready
 * - LED blinks briefly: Message received
 * 
 * - Check Serial Monitor for detailed logs
 * - Verify Raspberry Pi MQTT broker is running
 * - Test MQTT with: mosquitto_sub -h localhost -t "trap/#" -v
 */
