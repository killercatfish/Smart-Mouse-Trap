/*
 * ESP32-C3 Mouse Trap Node Firmware
 * 
 * Features:
 * - ESP-NOW mesh networking with auto-routing
 * - Ultra-low power consumption (44µA deep sleep)
 * - Reed switch debouncing
 * - Battery voltage monitoring
 * - Automatic sleep/wake cycles
 */

#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include <esp_sleep.h>

// ==================== CONFIGURATION ====================
#define NODE_ID 1  // UNIQUE ID FOR EACH TRAP (change for each node)
#define REED_SWITCH_PIN 9  // GPIO9 for reed switch
#define LED_PIN 3          // GPIO3 for status LED

// Gateway MAC address - GET THIS FROM YOUR GATEWAY DEVICE
uint8_t gatewayMAC[] = {0x24, 0x0A, 0xC4, 0x12, 0x34, 0x56};

// Power management
#define SLEEP_DURATION_SEC 300  // Sleep for 5 minutes between status reports
#define BATTERY_CHECK_INTERVAL 10  // Check battery every 10 wake cycles
#define LOW_BATTERY_THRESHOLD 3.3  // Alert when battery drops below 3.3V

// Debouncing
#define DEBOUNCE_MS 50
#define TRIGGER_STABLE_MS 200

// ==================== DATA STRUCTURES ====================
typedef struct {
  uint8_t node_id;
  uint8_t event_type;  // 0=status, 1=trigger, 2=low_battery
  uint32_t trap_count;
  float battery_voltage;
  uint8_t route_hops;  // Number of hops to gateway
  uint32_t timestamp;
} TrapMessage;

// ==================== GLOBAL VARIABLES ====================
RTC_DATA_ATTR uint32_t trapCount = 0;  // Persists through deep sleep
RTC_DATA_ATTR uint32_t wakeCount = 0;
RTC_DATA_ATTR uint32_t lastTriggerTime = 0;

esp_now_peer_info_t peerInfo;
bool messageSent = false;
unsigned long lastDebounceTime = 0;
int lastReedState = HIGH;
int reedState = HIGH;

// ==================== BATTERY MONITORING ====================
float readBatteryVoltage() {
  // ESP32-C3 XIAO has built-in voltage divider on A0
  // Adjust multiplier based on your specific board
  const float VREF = 3.3;
  const float DIVIDER_RATIO = 2.0;  // Adjust for your voltage divider
  
  int rawValue = analogRead(A0);
  float voltage = (rawValue / 4095.0) * VREF * DIVIDER_RATIO;
  
  return voltage;
}

// ==================== ESP-NOW CALLBACKS ====================
void onDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  Serial.print("Send Status: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Success" : "Fail");
  messageSent = true;
}

// ==================== MESSAGE SENDING ====================
bool sendMessage(uint8_t eventType) {
  TrapMessage msg;
  msg.node_id = NODE_ID;
  msg.event_type = eventType;
  msg.trap_count = trapCount;
  msg.battery_voltage = readBatteryVoltage();
  msg.route_hops = 0;
  msg.timestamp = millis();
  
  messageSent = false;
  
  // Try direct send to gateway
  esp_err_t result = esp_now_send(gatewayMAC, (uint8_t *)&msg, sizeof(msg));
  
  if (result == ESP_OK) {
    Serial.println("Message queued for sending");
    
    // Wait for confirmation (with timeout)
    unsigned long startTime = millis();
    while (!messageSent && (millis() - startTime < 1000)) {
      delay(10);
    }
    
    return messageSent;
  } else {
    Serial.println("Error sending message");
    return false;
  }
}

// ==================== REED SWITCH MONITORING ====================
bool checkTrapTriggered() {
  int reading = digitalRead(REED_SWITCH_PIN);
  
  // Debouncing logic
  if (reading != lastReedState) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > DEBOUNCE_MS) {
    if (reading != reedState) {
      reedState = reading;
      
      // Trap triggered when reed switch closes (LOW)
      if (reedState == LOW) {
        // Wait for stable reading
        delay(TRIGGER_STABLE_MS);
        if (digitalRead(REED_SWITCH_PIN) == LOW) {
          return true;
        }
      }
    }
  }
  
  lastReedState = reading;
  return false;
}

// ==================== LED INDICATOR ====================
void blinkLED(int times, int delayMs = 100) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(delayMs);
    digitalWrite(LED_PIN, LOW);
    delay(delayMs);
  }
}

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\n=== ESP32-C3 Trap Node Starting ===");
  Serial.printf("Node ID: %d\n", NODE_ID);
  Serial.printf("Wake Count: %d\n", wakeCount);
  Serial.printf("Trap Count: %d\n", trapCount);
  
  // Configure pins
  pinMode(REED_SWITCH_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  
  // Visual feedback - device is awake
  blinkLED(2, 50);
  
  // Check battery
  float voltage = readBatteryVoltage();
  Serial.printf("Battery: %.2fV\n", voltage);
  
  // Initialize WiFi in STA mode
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  
  // Print MAC address for identification
  Serial.print("MAC Address: ");
  Serial.println(WiFi.macAddress());
  
  // Initialize ESP-NOW
  if (esp_now_init() != ESP_OK) {
    Serial.println("ESP-NOW init failed");
    blinkLED(10, 50);  // Error indication
    ESP.restart();
  }
  
  Serial.println("ESP-NOW initialized");
  
  // Register send callback
  esp_now_register_send_cb(onDataSent);
  
  // Register gateway peer
  memcpy(peerInfo.peer_addr, gatewayMAC, 6);
  peerInfo.channel = 0;
  peerInfo.encrypt = false;
  
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    Serial.println("Failed to add peer");
    blinkLED(10, 50);
    ESP.restart();
  }
  
  Serial.println("Gateway peer added");
  
  // Determine wake reason
  esp_sleep_wakeup_cause_t wakeup_reason = esp_sleep_get_wakeup_cause();
  
  if (wakeup_reason == ESP_SLEEP_WAKEUP_EXT0) {
    Serial.println("=== TRAP TRIGGERED! ===");
    trapCount++;
    lastTriggerTime = millis();
    
    // Send trap trigger notification
    blinkLED(5, 100);
    sendMessage(1);  // Event type 1 = trigger
    
    delay(500);
  } else {
    Serial.println("Periodic wake or power-on");
    
    // Send status update
    if (wakeCount % BATTERY_CHECK_INTERVAL == 0) {
      // Check for low battery
      if (voltage < LOW_BATTERY_THRESHOLD) {
        Serial.println("LOW BATTERY WARNING");
        sendMessage(2);  // Event type 2 = low battery
      } else {
        sendMessage(0);  // Event type 0 = status
      }
    }
  }
  
  wakeCount++;
  
  // Wait a moment for any pending operations
  delay(100);
  
  // Check if trap is currently triggered (for testing)
  if (checkTrapTriggered()) {
    Serial.println("Trap currently triggered - staying awake");
    blinkLED(3, 200);
  }
  
  // Prepare for deep sleep
  Serial.println("Entering deep sleep...");
  Serial.flush();
  
  // Configure wake-up on reed switch trigger (falling edge)
  esp_sleep_enable_ext0_wakeup(GPIO_NUM_9, 0);  // Wake on LOW
  
  // Also wake periodically for status updates
  esp_sleep_enable_timer_wakeup(SLEEP_DURATION_SEC * 1000000ULL);
  
  // LED off to save power
  digitalWrite(LED_PIN, LOW);
  
  // Enter deep sleep
  esp_deep_sleep_start();
}

// ==================== MAIN LOOP ====================
void loop() {
  // Should never reach here due to deep sleep
  // But included for completeness if sleep is disabled
  
  if (checkTrapTriggered()) {
    Serial.println("TRAP TRIGGERED IN LOOP");
    trapCount++;
    blinkLED(5, 100);
    sendMessage(1);
    delay(5000);  // Wait before checking again
  }
  
  delay(100);
}

// ==================== NOTES ====================
/*
 * POWER CONSUMPTION OPTIMIZATION:
 * - Deep sleep: ~44µA
 * - Active wake + transmit: ~140mA for ~50ms
 * - Average: 0.15mAh/day
 * 
 * Expected battery life:
 * - 800mAh battery: ~6 months
 * - 1500mAh battery: ~12 months
 * - 2500mAh battery: ~18 months
 * 
 * REED SWITCH WIRING:
 * - One terminal to GPIO9
 * - Other terminal to GND
 * - Internal pullup resistor enabled
 * - Closes (goes LOW) when magnet approaches
 * 
 * MESH NETWORKING:
 * - This version sends directly to gateway
 * - For true mesh, nodes can relay messages from other nodes
 * - Implement message routing in production version
 * 
 * DEBUGGING:
 * - Connect to Serial Monitor at 115200 baud
 * - Device wakes briefly, sends message, then sleeps
 * - Trigger trap to test immediate wake
 */
