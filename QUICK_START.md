# Quick Start Guide
## Mouse Trap Monitoring System

**Get your smart trap system running in under 1 hour!**

---

## Overview

This system monitors mouse traps in real-time using:
- **ESP32-C3 nodes** on each trap (battery powered)
- **ESP32 gateway** (USB powered, bridges to WiFi)
- **Raspberry Pi server** (MQTT, database, web dashboard)
- **Telegram bot** for instant alerts

---

## Prerequisites

### Hardware Needed
- [ ] 1-3 ESP32-C3 boards (Seeed XIAO recommended)
- [ ] 1 ESP32 board (any model) for gateway
- [ ] Raspberry Pi (any model with WiFi)
- [ ] Victor M325 mouse traps
- [ ] MC-38 reed switches
- [ ] Small neodymium magnets
- [ ] LiPo batteries (800-2500mAh)
- [ ] USB cables and power supplies

### Software/Accounts Needed
- [ ] Arduino IDE or PlatformIO installed
- [ ] Telegram account (for bot notifications)
- [ ] SSH access to Raspberry Pi
- [ ] Text editor

---

## Step 1: Setup Telegram Bot (5 minutes)

### Create Bot

1. Open Telegram and message **@BotFather**
2. Send command: `/newbot`
3. Choose a name: "Mouse Trap Monitor"
4. Choose username: "YourNameTrapBot" (must end with 'bot')
5. Save the **bot token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Get Your Chat ID

1. Message **@userinfobot** on Telegram
2. It will reply with your chat ID (looks like: `123456789`)
3. Save this chat ID

### Test Bot

1. Start a chat with your bot (search for the username you created)
2. Send message: `/start`
3. Bot won't respond yet (that's ok - we'll configure it soon)

**Write these down:**
```
Bot Token: _________________________________
Chat ID:   _________________________________
```

---

## Step 2: Setup Raspberry Pi Server (15 minutes)

### Download Files

```bash
# SSH into your Raspberry Pi
ssh pi@raspberrypi.local

# Clone repository (or download files)
git clone https://github.com/yourusername/trap-monitor.git
cd trap-monitor/raspberry-pi
```

### Run Installation Script

```bash
chmod +x install.sh
sudo ./install.sh
```

This will:
- Install MQTT broker (Mosquitto)
- Install Python dependencies
- Create system services
- Setup database

### Configure System

Edit configuration file:
```bash
sudo nano /etc/trap-monitor/config.yaml
```

Update these fields:
```yaml
telegram:
  bot_token: "YOUR_BOT_TOKEN_HERE"
  chat_id: "YOUR_CHAT_ID_HERE"

node_locations:
  "1": "Kitchen"
  "2": "Garage"  
  "3": "Basement"
```

Save and exit (Ctrl+X, Y, Enter)

### Start Services

```bash
# Start all services
sudo systemctl start trap-mqtt-logger
sudo systemctl start trap-telegram-notifier
sudo systemctl start trap-dashboard

# Enable auto-start on boot
sudo systemctl enable trap-mqtt-logger
sudo systemctl enable trap-telegram-notifier
sudo systemctl enable trap-dashboard

# Check status
sudo systemctl status trap-mqtt-logger
```

### Verify MQTT Broker

Test MQTT is working:
```bash
# Terminal 1: Subscribe to messages
mosquitto_sub -h localhost -t "trap/#" -v

# Terminal 2: Send test message
mosquitto_pub -h localhost -t "trap/1/trigger" -m '{"node_id":1,"event_type":1,"trap_count":1,"battery_voltage":3.85}'
```

You should see the message appear in Terminal 1, and receive a Telegram notification!

---

## Step 3: Setup Gateway (10 minutes)

### Flash Gateway Firmware

**Option A: Using Arduino IDE**

1. Open `firmware/gateway/gateway.ino`
2. Install ESP32 board support:
   - File → Preferences
   - Additional Board Manager URLs: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools → Board → Board Manager → Search "esp32" → Install
3. Configure:
   - Tools → Board → "ESP32 Dev Module" (or your specific board)
   - Tools → Upload Speed → "921600"
   - Tools → Port → Select your ESP32's port
4. Edit WiFi credentials in `gateway.ino`:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
5. Edit MQTT server:
   ```cpp
   const char* mqtt_server = "raspberrypi.local"; // or IP address
   ```
6. Click Upload button

**Option B: Using PlatformIO**

```bash
cd firmware/gateway
pio run -t upload -t monitor
```

### Get Gateway MAC Address

1. Open Serial Monitor (115200 baud)
2. Look for line like: `MAC Address: 24:0A:C4:12:34:56`
3. **Write down this MAC address** - you'll need it for trap nodes

```
Gateway MAC: __ : __ : __ : __ : __ : __
```

### Verify Gateway

Gateway LED should:
- Stay ON = Connected to WiFi and MQTT
- Blink briefly = Message received
- Stay OFF = Connection issue (check serial monitor)

---

## Step 4: Assemble Trap Nodes (20 minutes each)

### Hardware Assembly

1. **Install Reed Switch:**
   - Hot glue reed switch to trap base
   - Position 5mm from striker bar

2. **Attach Magnet:**
   - Hot glue magnet to striker bar
   - Align over reed switch

3. **Wire Connections:**
   ```
   ESP32-C3 Pin → Reed Switch
   GPIO9 (D9)   → Reed switch terminal 1
   GND          → Reed switch terminal 2
   ```

4. **Test Reed Switch:**
   - Use multimeter in continuity mode
   - Trap open = OPEN circuit
   - Trap snapped = CLOSED circuit

5. **Mount ESP32-C3:**
   - Hot glue to side of trap
   - Keep USB port accessible

6. **Connect Battery:**
   - Plug LiPo battery into JST connector

### Flash Trap Node Firmware

**Edit Configuration First:**

Open `firmware/trap-node/trap-node.ino` and edit:

```cpp
#define NODE_ID 1  // CHANGE THIS FOR EACH NODE (1, 2, 3, etc.)

// Use the MAC address from Step 3
uint8_t gatewayMAC[] = {0x24, 0x0A, 0xC4, 0x12, 0x34, 0x56};
```

**Upload Firmware:**

Using Arduino IDE:
1. Tools → Board → "ESP32C3 Dev Module"
2. Upload

Using PlatformIO:
```bash
cd firmware/trap-node
pio run -t upload
```

### Test Node

1. Open Serial Monitor (115200 baud)
2. Should see:
   ```
   === ESP32-C3 Trap Node Starting ===
   Node ID: 1
   Battery: 3.85V
   ESP-NOW initialized
   ```
3. Manually trigger reed switch with magnet
4. Should see: `TRAP TRIGGERED!`
5. Check Raspberry Pi receives MQTT message
6. You should get a Telegram notification!

---

## Step 5: Access Dashboard (2 minutes)

### Open Dashboard

In your web browser, go to:
```
http://raspberrypi.local:5000
```

Or use IP address:
```
http://192.168.1.XXX:5000
```

### What You Should See

- **Total Catches**: Current count
- **Active Traps**: Number of online nodes
- **Catches (24h)**: Recent activity
- **Node Cards**: Status of each trap
- **Recent Events**: Live event feed

---

## Step 6: Deploy and Test (10 minutes)

### Deploy Traps

1. Place traps in desired locations
2. Set traps carefully
3. Add bait (peanut butter recommended)
4. Verify each node appears in dashboard

### Test System End-to-End

For each node:

1. **Trigger Trap:**
   - Manually snap trap (carefully!)
   - Or use magnet to trigger reed switch

2. **Verify Notifications:**
   - Check dashboard updates immediately
   - Telegram notification received within 1 second
   - Event logged in database

3. **Check Status:**
   - Node shows as "Online" in dashboard
   - Battery voltage displayed
   - Last seen time updated

---

## Troubleshooting

### Gateway Not Connecting to WiFi

**Symptoms:** Gateway LED off
**Solutions:**
- Check WiFi credentials in code
- Verify WiFi network is 2.4GHz (not 5GHz)
- Check router settings (allow new devices)
- Try moving gateway closer to router

### Trap Node Not Reporting

**Symptoms:** No MQTT messages from node
**Solutions:**
- Verify gateway MAC address in node firmware
- Check battery voltage (should be >3.3V)
- Test reed switch with multimeter
- Re-flash firmware with correct NODE_ID
- Check serial monitor for error messages

### No Telegram Notifications

**Symptoms:** Dashboard works but no Telegram alerts
**Solutions:**
- Verify bot token in config.yaml
- Verify chat ID in config.yaml
- Check service status: `sudo systemctl status trap-telegram-notifier`
- View logs: `sudo tail -f /var/log/trap-monitor/telegram-notifier.log`
- Test bot manually in Telegram

### Dashboard Not Loading

**Symptoms:** Can't access web page
**Solutions:**
- Check service: `sudo systemctl status trap-dashboard`
- Verify Raspberry Pi IP address
- Check firewall settings
- Try: `http://IP-ADDRESS:5000` instead of hostname

---

## System Maintenance

### Daily
- [ ] Check dashboard for activity
- [ ] Verify all nodes online

### Weekly
- [ ] Review catch statistics
- [ ] Test Telegram notifications

### Monthly
- [ ] Check battery voltages
- [ ] Clean reed switches
- [ ] Backup database

### As Needed
- [ ] Replace batteries (<3.3V)
- [ ] Reset/rebait traps
- [ ] Update firmware

---

## Next Steps

### Optimize Your System

1. **Adjust Locations:**
   - Edit `/etc/trap-monitor/config.yaml`
   - Add custom names for each node

2. **Customize Notifications:**
   - Change notification intervals
   - Disable status updates
   - Add more details to messages

3. **Add More Nodes:**
   - Flash firmware with unique NODE_ID
   - Update config.yaml locations
   - Deploy and monitor

4. **Monitor Performance:**
   - Track battery life
   - Review catch patterns
   - Optimize trap placement

### Advanced Features

- **Mesh Networking:** Nodes auto-relay for extended range
- **Data Analysis:** Export data for trend analysis
- **Remote Access:** Setup port forwarding for external access
- **Mobile App:** Use Telegram or build custom app
- **Email Alerts:** Add email notifications
- **Voice Alerts:** Integrate with smart home systems

---

## Useful Commands

### Check Service Status
```bash
sudo systemctl status trap-mqtt-logger
sudo systemctl status trap-telegram-notifier
sudo systemctl status trap-dashboard
```

### View Logs
```bash
# Live log tail
sudo tail -f /var/log/trap-monitor/*.log

# View full log
sudo less /var/log/trap-monitor/mqtt-logger.log
```

### Restart Services
```bash
sudo systemctl restart trap-mqtt-logger
sudo systemctl restart trap-telegram-notifier
sudo systemctl restart trap-dashboard
```

### MQTT Debug
```bash
# Monitor all trap messages
mosquitto_sub -h localhost -t "trap/#" -v

# Send test trigger
mosquitto_pub -h localhost -t "trap/1/trigger" -m '{"node_id":1,"event_type":1,"trap_count":5,"battery_voltage":3.85}'
```

### Database Queries
```bash
sqlite3 /var/lib/trap-monitor/trap_events.db

# View recent events
SELECT * FROM trap_events ORDER BY received_at DESC LIMIT 10;

# Count triggers per node
SELECT node_id, COUNT(*) FROM trap_events WHERE event_type=1 GROUP BY node_id;

# Battery status
SELECT node_id, battery_voltage, last_seen FROM node_status;
```

---

## Getting Help

### Check Logs First
Most issues can be diagnosed from logs:
```bash
sudo journalctl -u trap-mqtt-logger -f
sudo journalctl -u trap-telegram-notifier -f
```

### Common Issues

| Issue | Check | Solution |
|-------|-------|----------|
| No notifications | Telegram config | Verify bot token and chat ID |
| Node offline | Battery | Charge or replace battery |
| No messages | MAC address | Update gateway MAC in firmware |
| Dashboard blank | Services | Restart services |

### Resources

- **GitHub Repository:** [Link to your repo]
- **Documentation:** See README.md and HARDWARE_GUIDE.md
- **Community:** [Forum/Discord link]
- **Issues:** Report bugs on GitHub Issues

---

## Congratulations!

Your mouse trap monitoring system is now operational! 🎉

You'll receive instant notifications whenever a trap is triggered, can monitor all traps from a single dashboard, and track long-term patterns in rodent activity.

**Happy trapping!** 🪤
