#!/bin/bash
#
# Installation Script for Mouse Trap Monitoring System
# Run with: sudo ./install.sh
#

set -e  # Exit on error

echo "=================================================="
echo "  Mouse Trap Monitoring System - Installation"
echo "=================================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
   echo "ERROR: Please run as root (use sudo)"
   exit 1
fi

echo "[1/8] Updating system packages..."
apt update
apt upgrade -y

echo "[2/8] Installing dependencies..."
apt install -y \
    mosquitto \
    mosquitto-clients \
    python3 \
    python3-pip \
    python3-venv \
    sqlite3 \
    git

echo "[3/8] Setting up Mosquitto MQTT broker..."
systemctl enable mosquitto
systemctl start mosquitto

# Configure Mosquitto (basic setup)
cat > /etc/mosquitto/conf.d/trap-monitor.conf << 'EOF'
# Trap Monitor MQTT Configuration
listener 1883
allow_anonymous true

# For production, enable authentication:
# allow_anonymous false
# password_file /etc/mosquitto/passwd
EOF

systemctl restart mosquitto
echo "✓ MQTT broker running on port 1883"

echo "[4/8] Creating system user and directories..."
# Create user
useradd -r -s /bin/false -d /opt/trap-monitor trapmonitor || true

# Create directories
mkdir -p /opt/trap-monitor
mkdir -p /var/lib/trap-monitor
mkdir -p /var/log/trap-monitor
mkdir -p /etc/trap-monitor

# Set ownership
chown -R trapmonitor:trapmonitor /opt/trap-monitor
chown -R trapmonitor:trapmonitor /var/lib/trap-monitor
chown -R trapmonitor:trapmonitor /var/log/trap-monitor
chown -R trapmonitor:trapmonitor /etc/trap-monitor

echo "[5/8] Installing Python dependencies..."
# Create virtual environment
python3 -m venv /opt/trap-monitor/venv
source /opt/trap-monitor/venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install \
    paho-mqtt \
    flask \
    flask-socketio \
    python-socketio \
    python-telegram-bot \
    pyyaml

deactivate

echo "[6/8] Copying application files..."
# Copy Python scripts
cp mqtt_logger.py /opt/trap-monitor/
cp telegram_notifier.py /opt/trap-monitor/
cp dashboard.py /opt/trap-monitor/
chmod +x /opt/trap-monitor/*.py

# Copy configuration
cp config.yaml /etc/trap-monitor/

# Set ownership
chown -R trapmonitor:trapmonitor /opt/trap-monitor
chown trapmonitor:trapmonitor /etc/trap-monitor/config.yaml

echo "[7/8] Creating systemd services..."

# MQTT Logger Service
cat > /etc/systemd/system/trap-mqtt-logger.service << 'EOF'
[Unit]
Description=Mouse Trap MQTT Logger
After=mosquitto.service network.target
Wants=mosquitto.service

[Service]
Type=simple
User=trapmonitor
Group=trapmonitor
WorkingDirectory=/opt/trap-monitor
ExecStart=/opt/trap-monitor/venv/bin/python3 /opt/trap-monitor/mqtt_logger.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/trap-monitor/mqtt-logger.log
StandardError=append:/var/log/trap-monitor/mqtt-logger.log

[Install]
WantedBy=multi-user.target
EOF

# Telegram Notifier Service
cat > /etc/systemd/system/trap-telegram-notifier.service << 'EOF'
[Unit]
Description=Mouse Trap Telegram Notifier
After=mosquitto.service network-online.target
Wants=mosquitto.service network-online.target

[Service]
Type=simple
User=trapmonitor
Group=trapmonitor
WorkingDirectory=/opt/trap-monitor
ExecStart=/opt/trap-monitor/venv/bin/python3 /opt/trap-monitor/telegram_notifier.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/trap-monitor/telegram-notifier.log
StandardError=append:/var/log/trap-monitor/telegram-notifier.log

[Install]
WantedBy=multi-user.target
EOF

# Flask Dashboard Service
cat > /etc/systemd/system/trap-dashboard.service << 'EOF'
[Unit]
Description=Mouse Trap Web Dashboard
After=network.target

[Service]
Type=simple
User=trapmonitor
Group=trapmonitor
WorkingDirectory=/opt/trap-monitor
ExecStart=/opt/trap-monitor/venv/bin/python3 /opt/trap-monitor/dashboard.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/trap-monitor/dashboard.log
StandardError=append:/var/log/trap-monitor/dashboard.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo "[8/8] Configuration..."
echo ""
echo "=================================================="
echo "  Installation Complete!"
echo "=================================================="
echo ""
echo "⚠️  IMPORTANT: Configure before starting services"
echo ""
echo "1. Edit configuration file:"
echo "   sudo nano /etc/trap-monitor/config.yaml"
echo ""
echo "   - Add your Telegram bot token"
echo "   - Add your Telegram chat ID"
echo "   - Customize node locations"
echo ""
echo "2. Get Telegram credentials:"
echo "   Bot Token: Talk to @BotFather on Telegram"
echo "   Chat ID: Talk to @userinfobot on Telegram"
echo ""
echo "3. Start services:"
echo "   sudo systemctl start trap-mqtt-logger"
echo "   sudo systemctl start trap-telegram-notifier"
echo "   sudo systemctl start trap-dashboard"
echo ""
echo "4. Enable auto-start on boot:"
echo "   sudo systemctl enable trap-mqtt-logger"
echo "   sudo systemctl enable trap-telegram-notifier"
echo "   sudo systemctl enable trap-dashboard"
echo ""
echo "5. Check service status:"
echo "   sudo systemctl status trap-mqtt-logger"
echo "   sudo systemctl status trap-telegram-notifier"
echo "   sudo systemctl status trap-dashboard"
echo ""
echo "6. View logs:"
echo "   sudo tail -f /var/log/trap-monitor/*.log"
echo ""
echo "7. Access web dashboard:"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo "   or"
echo "   http://raspberrypi.local:5000"
echo ""
echo "=================================================="
echo "  Testing MQTT"
echo "=================================================="
echo ""
echo "Test MQTT with:"
echo "  mosquitto_sub -h localhost -t 'trap/#' -v"
echo ""
echo "Send test message:"
echo '  mosquitto_pub -h localhost -t "trap/1/trigger" -m '"'"'{"node_id":1,"event_type":1,"trap_count":1,"battery_voltage":3.85}'"'"''
echo ""
echo "=================================================="
