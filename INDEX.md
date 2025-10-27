# 🪤 Smart Mouse Trap Monitoring System
## Complete Project Files

**All artifacts generated and ready to use!**

---

## 📚 Start Here

1. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete system overview (READ THIS FIRST!)
2. **[QUICK_START.md](QUICK_START.md)** - Get up and running in under 1 hour
3. **[README.md](README.md)** - Main documentation with features and API
4. **[HARDWARE_GUIDE.md](HARDWARE_GUIDE.md)** - Assembly instructions and wiring diagrams

---

## 📁 Project Structure

```
trap-monitor/
├── README.md                      # Main documentation
├── PROJECT_SUMMARY.md             # Complete overview
├── QUICK_START.md                 # Setup guide
├── HARDWARE_GUIDE.md              # Assembly instructions
│
├── firmware/                      # ESP32 Firmware
│   ├── platformio.ini            # Build configuration
│   ├── trap-node/
│   │   └── trap-node.ino         # Battery-powered node
│   └── gateway/
│       └── gateway.ino           # USB-powered gateway
│
└── raspberry-pi/                  # Server Software
    ├── install.sh                # Automated installer
    ├── config.yaml               # Configuration file
    ├── mqtt_logger.py            # Database logger
    ├── telegram_notifier.py      # Alert service
    ├── dashboard.py              # Web server
    └── templates/
        └── dashboard.html        # Web UI
```

---

## 🎯 System Overview

### Components
- **Trap Nodes** (ESP32-C3): Battery-powered, attach to mouse traps
- **Gateway** (ESP32): USB-powered, bridges ESP-NOW to WiFi/MQTT
- **Server** (Raspberry Pi): MQTT broker, database, web dashboard, notifications

### Features
- ⚡ Instant notifications (sub-200ms)
- 🔋 6-12 month battery life
- 📡 Mesh networking extends range
- 📊 Real-time web dashboard
- 💰 $10 per trap node

---

## 🚀 Quick Deploy

### 1. Setup Raspberry Pi (15 min)
```bash
cd raspberry-pi/
chmod +x install.sh
sudo ./install.sh
sudo nano /etc/trap-monitor/config.yaml  # Add Telegram credentials
sudo systemctl start trap-*
```

### 2. Flash Gateway (10 min)
- Open `firmware/gateway/gateway.ino`
- Configure WiFi credentials
- Upload to ESP32
- Note MAC address from serial monitor

### 3. Flash Trap Nodes (20 min each)
- Open `firmware/trap-node/trap-node.ino`
- Set NODE_ID (1, 2, 3, etc.)
- Set gateway MAC address
- Upload to ESP32-C3
- Assemble hardware (see HARDWARE_GUIDE.md)

### 4. Access Dashboard
```
http://raspberrypi.local:5000
```

---

## 💰 Bill of Materials

### Per Trap Node ($10-12)
- ESP32-C3 board: $4-5
- Victor M325 trap: $0.64-1
- Reed switch + magnet: $0.50
- LiPo battery: $4-6
- Wire, hot glue: $1

### Gateway (one-time)
- ESP32 board: $3-5
- USB power: $3-5

### Server (one-time)
- Raspberry Pi: $15-50
- MicroSD card: $5-10

**Total starter kit (3 traps): ~$96**

---

## 📖 Documentation Guide

### For First-Time Users
1. Read **PROJECT_SUMMARY.md** for complete overview
2. Follow **QUICK_START.md** step-by-step
3. Reference **HARDWARE_GUIDE.md** during assembly

### For Experienced Users
1. Skim **README.md** for architecture
2. Configure `config.yaml`
3. Flash firmware with your settings
4. Deploy and test

### For Developers
- Review firmware source code in `firmware/`
- Examine Python services in `raspberry-pi/`
- Check `platformio.ini` for build options
- Modify `dashboard.html` for UI changes

---

## 🔧 Key Configuration Files

### config.yaml (Raspberry Pi)
```yaml
telegram:
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"

node_locations:
  "1": "Kitchen"
  "2": "Garage"
  "3": "Basement"
```

### trap-node.ino (Each Trap)
```cpp
#define NODE_ID 1  // Change for each node
uint8_t gatewayMAC[] = {0x24, 0x0A, 0xC4, 0x12, 0x34, 0x56};
```

### gateway.ino (Gateway)
```cpp
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";
const char* mqtt_server = "raspberrypi.local";
```

---

## 📊 System Requirements

### Hardware
- ESP32-C3 or compatible (trap nodes)
- ESP32 any variant (gateway)
- Raspberry Pi 3B+ or newer
- Victor M325 mouse traps
- MC-38 reed switches
- LiPo batteries (800-2500mAh)

### Software
- Arduino IDE or PlatformIO
- Python 3.7+
- Mosquitto MQTT broker
- Flask + dependencies
- Telegram bot account

---

## 🎓 What You'll Learn

Building this project teaches:
- ESP-NOW mesh networking
- MQTT pub/sub architecture
- Flask web development
- Real-time WebSocket communication
- SQLite database design
- Linux systemd services
- Power-efficient IoT design
- Reed switch sensors

---

## 🐛 Troubleshooting

### Common Issues

**Gateway won't connect to WiFi**
- Check WiFi credentials
- Verify 2.4GHz network (not 5GHz)
- Move gateway closer to router

**Trap node not reporting**
- Verify gateway MAC address in firmware
- Check battery voltage (>3.3V required)
- Test reed switch with multimeter

**No Telegram notifications**
- Verify bot token and chat ID
- Check service status: `systemctl status trap-telegram-notifier`
- View logs: `tail -f /var/log/trap-monitor/*.log`

**Dashboard won't load**
- Check service: `systemctl status trap-dashboard`
- Try IP address instead of hostname
- Verify port 5000 not blocked

---

## 🎯 Next Steps After Setup

1. **Test the system**
   - Manually trigger each trap
   - Verify notifications arrive
   - Check dashboard updates

2. **Optimize placement**
   - Position traps in high-activity areas
   - Ensure good mesh network coverage
   - Monitor signal strength

3. **Customize**
   - Edit node locations in config.yaml
   - Adjust notification preferences
   - Modify dashboard appearance

4. **Scale up**
   - Add more trap nodes as needed
   - Each node costs only $10-12
   - Mesh network auto-extends range

---

## 📞 Support

### Documentation
- **PROJECT_SUMMARY.md** - Complete system overview
- **QUICK_START.md** - Step-by-step setup
- **HARDWARE_GUIDE.md** - Assembly details
- **README.md** - Technical reference

### Getting Help
1. Check documentation first
2. Review service logs
3. Test MQTT with command line
4. Open GitHub issue with details

---

## ⚡ Quick Commands

### Check service status
```bash
sudo systemctl status trap-mqtt-logger
sudo systemctl status trap-telegram-notifier
sudo systemctl status trap-dashboard
```

### View logs
```bash
sudo tail -f /var/log/trap-monitor/*.log
```

### Test MQTT
```bash
# Monitor messages
mosquitto_sub -h localhost -t "trap/#" -v

# Send test
mosquitto_pub -h localhost -t "trap/1/trigger" -m '{"node_id":1,"event_type":1,"trap_count":1,"battery_voltage":3.85}'
```

### Query database
```bash
sqlite3 /var/lib/trap-monitor/trap_events.db "SELECT * FROM trap_events ORDER BY received_at DESC LIMIT 10;"
```

---

## 📄 License

MIT License - Free for personal and commercial use

---

## 🎉 Ready to Build!

Everything you need is in this package. Start with **QUICK_START.md** and you'll have a working system in under an hour!

**Happy trapping!** 🪤

---

*Built with ❤️ for practical IoT monitoring*
