#!/usr/bin/env python3
"""
Telegram Notifier for Mouse Trap Monitoring System
Sends instant notifications via Telegram when traps are triggered
"""

import paho.mqtt.client as mqtt
import json
import yaml
import logging
import sys
import signal
from datetime import datetime
import asyncio
from telegram import Bot
from telegram.error import TelegramError

# Configuration file
CONFIG_FILE = "/etc/trap-monitor/config.yaml"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/trap-monitor/telegram-notifier.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Handle Telegram notifications for trap events"""
    
    def __init__(self, config):
        self.config = config
        self.bot = Bot(token=config['telegram']['bot_token'])
        self.chat_id = config['telegram']['chat_id']
        self.mqtt_broker = config['mqtt']['broker']
        self.mqtt_port = config['mqtt']['port']
        
        # Notification preferences
        self.notify_on_trigger = config['notifications'].get('on_trigger', True)
        self.notify_on_low_battery = config['notifications'].get('on_low_battery', True)
        self.notify_on_status = config['notifications'].get('on_status', False)
        
        # Rate limiting (prevent spam)
        self.last_notification_time = {}
        self.min_notification_interval = config['notifications'].get('min_interval_seconds', 10)
        
        # Setup MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            client.subscribe("trap/#")
            logger.info("Subscribed to trap topics")
            
            # Send startup notification
            asyncio.run(self.send_message("🟢 Trap Monitor System Online"))
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker")
    
    def should_notify(self, node_id, event_type):
        """Check if we should send notification (rate limiting)"""
        key = f"{node_id}_{event_type}"
        current_time = datetime.now().timestamp()
        
        if key in self.last_notification_time:
            time_since_last = current_time - self.last_notification_time[key]
            if time_since_last < self.min_notification_interval:
                logger.debug(f"Rate limit: Skipping notification for {key}")
                return False
        
        self.last_notification_time[key] = current_time
        return True
    
    def format_trap_message(self, data):
        """Format trap trigger message"""
        node_id = data.get('node_id', 'Unknown')
        trap_count = data.get('trap_count', 0)
        battery = data.get('battery_voltage', 0)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Node location mapping (customize this)
        locations = self.config.get('node_locations', {})
        location = locations.get(str(node_id), f"Node {node_id}")
        
        message = f"🪤 **MOUSE TRAP TRIGGERED!**\n\n"
        message += f"📍 Location: {location}\n"
        message += f"🔢 Node ID: {node_id}\n"
        message += f"📊 Total Catches: {trap_count}\n"
        message += f"🔋 Battery: {battery:.2f}V\n"
        message += f"🕐 Time: {timestamp}"
        
        return message
    
    def format_low_battery_message(self, data):
        """Format low battery warning message"""
        node_id = data.get('node_id', 'Unknown')
        battery = data.get('battery_voltage', 0)
        
        locations = self.config.get('node_locations', {})
        location = locations.get(str(node_id), f"Node {node_id}")
        
        message = f"🔋 **LOW BATTERY WARNING**\n\n"
        message += f"📍 Location: {location}\n"
        message += f"🔢 Node ID: {node_id}\n"
        message += f"⚡ Voltage: {battery:.2f}V\n"
        message += f"⚠️ Please replace battery soon"
        
        return message
    
    def format_status_message(self, data):
        """Format status update message"""
        node_id = data.get('node_id', 'Unknown')
        battery = data.get('battery_voltage', 0)
        trap_count = data.get('trap_count', 0)
        
        locations = self.config.get('node_locations', {})
        location = locations.get(str(node_id), f"Node {node_id}")
        
        message = f"ℹ️ **Status Update**\n\n"
        message += f"📍 {location}\n"
        message += f"🔋 {battery:.2f}V | "
        message += f"📊 {trap_count} catches"
        
        return message
    
    async def send_message(self, text):
        """Send message via Telegram"""
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode='Markdown'
            )
            logger.info("Telegram notification sent successfully")
            return True
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            payload = json.loads(msg.payload.decode())
            event_type = payload.get('event_type')
            node_id = payload.get('node_id')
            
            logger.info(f"Received event: Type {event_type}, Node {node_id}")
            
            # Check rate limiting
            if not self.should_notify(node_id, event_type):
                return
            
            # Handle different event types
            if event_type == 1 and self.notify_on_trigger:
                # Trap triggered
                message = self.format_trap_message(payload)
                asyncio.run(self.send_message(message))
                
            elif event_type == 2 and self.notify_on_low_battery:
                # Low battery
                message = self.format_low_battery_message(payload)
                asyncio.run(self.send_message(message))
                
            elif event_type == 0 and self.notify_on_status:
                # Status update (usually disabled)
                message = self.format_status_message(payload)
                asyncio.run(self.send_message(message))
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def start(self):
        """Start the notifier"""
        try:
            logger.info("Starting Telegram Notifier...")
            self.client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.stop()
        except Exception as e:
            logger.error(f"Error starting notifier: {e}")
            raise
    
    def stop(self):
        """Stop the notifier"""
        logger.info("Stopping Telegram Notifier...")
        asyncio.run(self.send_message("🔴 Trap Monitor System Offline"))
        self.client.disconnect()
        self.client.loop_stop()

def load_config():
    """Load configuration from YAML file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
        logger.info("Configuration loaded successfully")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {CONFIG_FILE}")
        # Return default config
        return {
            'telegram': {
                'bot_token': 'YOUR_BOT_TOKEN_HERE',
                'chat_id': 'YOUR_CHAT_ID_HERE'
            },
            'mqtt': {
                'broker': 'localhost',
                'port': 1883
            },
            'notifications': {
                'on_trigger': True,
                'on_low_battery': True,
                'on_status': False,
                'min_interval_seconds': 10
            },
            'node_locations': {
                '1': 'Kitchen',
                '2': 'Garage',
                '3': 'Basement'
            }
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received")
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load configuration
    config = load_config()
    
    # Start notifier
    logger.info("=== Telegram Notifier Starting ===")
    notifier = TelegramNotifier(config)
    notifier.start()
