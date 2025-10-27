# ESP32-C3 Mouse Trap Monitoring System

**Real-time mouse trap monitoring with ESP-NOW mesh networking, MQTT, and web dashboard**

## Features

- 🐭 **Instant Alerts**: Sub-200ms trap trigger notifications via Telegram
- 🔋 **Ultra-Low Power**: 6-12 month battery life on single charge
- 📡 **Mesh Network**: ESP-NOW auto-routing extends range beyond WiFi
- 📊 **Real-Time Dashboard**: Live web interface with SocketIO updates
- 💾 **Historical Data**: SQLite database with trend analysis
- 🔌 **Easy Setup**: Complete deployment scripts and documentation

## Hardware Requirements

### Per Trap Node ($8-12 each)
- ESP32-C3 development board (Seeed XIAO ESP32-C3 or similar) - $3-5
- Victor M325 mouse trap - $0.64-1.00
- MC-38 reed switch - $0.30-0.50
- 6mm × 3mm neodymium magnet - $0.20
- 800-2500mAh LiPo battery with JST connector - $4-6
- Hot glue, wires, heat shrink tubing

### Gateway (Single Unit)
- ESP32 or ESP32-C3 development board - $3-5
- USB power adapter

### Server
- Raspberry Pi (any model with WiFi) - $15-50
- MicroSD card (8GB+) - $5-10

## System Architecture

```
┌─────────────┐     ESP-NOW Mesh     ┌─────────────┐
│  Trap Node  │◄────────────────────►│  Trap Node  │
│   (ESP32)   │                      │   (ESP32)   │
└──────┬──────┘                      └──────┬──────┘
       │                                    │
       │         ESP-NOW Mesh               │
       └────────────┬───────────────────────┘
                    │
              ┌─────▼─────┐
              │  Gateway  │ WiFi
              │  (ESP32)  │◄────────┐
              └─────┬─────┘         │
                    │ MQTT          │
              ┌─────▼──────────┐    │
              │  Raspberry Pi  │◄───┘
              │  - MQTT Broker │
              │  - Database    │
              │  - Flask App   │
              │  - Telegram    │
              └────────────────┘
```

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/esp32-trap-monitor.git
cd esp32-trap-monitor
```

### 2. Setup Raspberry Pi Server
```bash
cd raspberry-pi
chmod +x install.sh
sudo ./install.sh
```

Edit configuration:
```bash
nano config.yaml
# Add your Telegram bot token and chat ID
```

### 3. Flash ESP32-C3 Trap Nodes

**Using PlatformIO:**
```bash
cd firmware/trap-node
pio run -t upload
```

**Using Arduino IDE:**
1. Open `firmware/trap-node/trap-node.ino`
2. Edit `config.h` with your gateway MAC address
3. Select "ESP32C3 Dev Module" board
4. Upload

### 4. Flash ESP32 Gateway
```bash
cd firmware/gateway
pio run -t upload
```

### 5. Access Dashboard
Open browser to: `http://raspberrypi.local:5000`

## Hardware Assembly

### Trap Node Wiring

```
ESP32-C3 Pinout:
├─ D9 (GPIO9)  → Reed Switch (one terminal)
├─ GND         → Reed Switch (other terminal)
├─ 3V3         → Status LED (with 220Ω resistor)
└─ BAT+/BAT-   → LiPo battery JST connector

Reed Switch Installation:
1. Hot glue reed switch to trap base near striker bar pivot
2. Hot glue magnet to striker bar
3. Test trigger: LED should blink when trap snaps
```

### Gateway Wiring
```
ESP32 Gateway:
├─ Connected via USB power (always on)
└─ No external components needed
```

## Software Configuration

### Raspberry Pi Setup

**1. Install dependencies:**
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients python3-pip
pip3 install paho-mqtt flask flask-socketio python-telegram-bot pyyaml
```

**2. Configure Telegram Bot:**
```bash
# Talk to @BotFather on Telegram
# Create new bot and get token
# Get your chat ID from @userinfobot

# Edit config.yaml
nano config.yaml
```

**3. Start services:**
```bash
sudo systemctl enable trap-monitor
sudo systemctl start trap-monitor
```

### ESP32 Firmware Configuration

Edit `firmware/trap-node/config.h`:
```cpp
#define NODE_ID 1  // Unique ID for each trap
#define GATEWAY_MAC {0x24, 0x0A, 0xC4, 0xXX, 0xXX, 0xXX}  // Gateway MAC address
```

## Testing

### 1. Monitor MQTT Messages
```bash
mosquitto_sub -h localhost -t "trap/#" -v
```

### 2. Test Database
```bash
sqlite3 /var/lib/trap-monitor/trap_events.db
SELECT * FROM trap_events ORDER BY timestamp DESC LIMIT 10;
```

### 3. Verify Telegram
Trigger a trap and verify you receive a message within 1 second.

## Battery Life Optimization

**Expected battery life:**
- 800mAh: 6 months
- 1500mAh: 12 months
- 2500mAh: 18+ months

**Power consumption:**
- Deep sleep: 44µA
- Wake + transmit: 140mA for 50ms
- Average: ~0.15mAh per day

## Troubleshooting

### Trap not reporting
1. Check battery voltage (should be >3.3V)
2. Verify MAC address in firmware matches gateway
3. Check reed switch alignment with magnet

### No Telegram notifications
1. Verify bot token in config.yaml
2. Check chat ID is correct
3. Ensure Raspberry Pi has internet connection

### Mesh network issues
1. Ensure nodes are within 30-50m of each other
2. Check for WiFi interference (change ESP-NOW channel)
3. Verify all nodes have correct gateway MAC

## API Reference

### MQTT Topics

```
trap/{node_id}/status    - Node status updates
trap/{node_id}/trigger   - Trap trigger events
trap/{node_id}/battery   - Battery voltage reports
gateway/status           - Gateway status
```

### REST API Endpoints

```
GET  /api/traps          - List all traps
GET  /api/events         - Get recent events
GET  /api/stats          - Get statistics
POST /api/trap/{id}/test - Test trap notification
```

## License

MIT License - See LICENSE file for details

## Contributing

Pull requests welcome! Please open an issue first to discuss changes.

## Support

- GitHub Issues: [Report bugs](https://github.com/yourusername/esp32-trap-monitor/issues)
- Discussions: [Ask questions](https://github.com/yourusername/esp32-trap-monitor/discussions)
