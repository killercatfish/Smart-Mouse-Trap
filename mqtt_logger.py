#!/usr/bin/env python3
"""
MQTT Logger for Mouse Trap Monitoring System
Subscribes to MQTT topics and logs events to SQLite database
"""

import paho.mqtt.client as mqtt
import json
import sqlite3
from datetime import datetime
import logging
import sys
import signal

# Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "trap/#"
DATABASE_PATH = "/var/lib/trap-monitor/trap_events.db"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/trap-monitor/mqtt-logger.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TrapDatabase:
    """Handle database operations for trap events"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trap_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id INTEGER NOT NULL,
                    event_type INTEGER NOT NULL,
                    event_type_str TEXT NOT NULL,
                    trap_count INTEGER,
                    battery_voltage REAL,
                    route_hops INTEGER,
                    timestamp INTEGER,
                    gateway_time INTEGER,
                    mac_address TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(node_id, timestamp)
                )
            ''')
            
            # Node status table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS node_status (
                    node_id INTEGER PRIMARY KEY,
                    mac_address TEXT,
                    last_seen TIMESTAMP,
                    last_event_type TEXT,
                    total_triggers INTEGER DEFAULT 0,
                    battery_voltage REAL,
                    is_online BOOLEAN DEFAULT 1
                )
            ''')
            
            # Statistics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_triggers INTEGER DEFAULT 0,
                    active_nodes INTEGER DEFAULT 0,
                    UNIQUE(date)
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_node_id 
                ON trap_events(node_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON trap_events(received_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_type 
                ON trap_events(event_type)
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def insert_event(self, data):
        """Insert trap event into database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert event
            cursor.execute('''
                INSERT OR IGNORE INTO trap_events 
                (node_id, event_type, event_type_str, trap_count, battery_voltage, 
                 route_hops, timestamp, gateway_time, mac_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('node_id'),
                data.get('event_type'),
                data.get('event_type_str'),
                data.get('trap_count'),
                data.get('battery_voltage'),
                data.get('route_hops'),
                data.get('timestamp'),
                data.get('gateway_time'),
                data.get('mac_address')
            ))
            
            # Update node status
            cursor.execute('''
                INSERT OR REPLACE INTO node_status 
                (node_id, mac_address, last_seen, last_event_type, 
                 total_triggers, battery_voltage, is_online)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, 
                        COALESCE((SELECT total_triggers FROM node_status WHERE node_id = ?), 0) + ?,
                        ?, 1)
            ''', (
                data.get('node_id'),
                data.get('mac_address'),
                data.get('event_type_str'),
                data.get('node_id'),
                1 if data.get('event_type') == 1 else 0,  # Increment only for trigger events
                data.get('battery_voltage')
            ))
            
            # Update daily statistics for trigger events
            if data.get('event_type') == 1:
                today = datetime.now().date()
                cursor.execute('''
                    INSERT INTO statistics (date, total_triggers, active_nodes)
                    VALUES (?, 1, 1)
                    ON CONFLICT(date) DO UPDATE SET
                        total_triggers = total_triggers + 1
                ''', (today,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Event logged: Node {data.get('node_id')}, Type: {data.get('event_type_str')}")
            return True
            
        except Exception as e:
            logger.error(f"Database insert error: {e}")
            return False

class MQTTLogger:
    """MQTT client for receiving and logging trap events"""
    
    def __init__(self):
        self.db = TrapDatabase(DATABASE_PATH)
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            client.subscribe(MQTT_TOPIC)
            logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects"""
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker")
    
    def on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        try:
            # Parse JSON payload
            payload = json.loads(msg.payload.decode())
            
            logger.info(f"Received message on {msg.topic}")
            logger.debug(f"Payload: {payload}")
            
            # Log to database
            self.db.insert_event(payload)
            
            # Special handling for trigger events
            if payload.get('event_type') == 1:
                logger.warning(f"🪤 TRAP TRIGGERED! Node {payload.get('node_id')}, "
                             f"Count: {payload.get('trap_count')}")
            
            # Low battery warnings
            if payload.get('event_type') == 2:
                logger.warning(f"🔋 LOW BATTERY! Node {payload.get('node_id')}, "
                             f"Voltage: {payload.get('battery_voltage')}V")
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def start(self):
        """Start the MQTT client"""
        try:
            logger.info("Starting MQTT Logger...")
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.stop()
        except Exception as e:
            logger.error(f"Error starting MQTT client: {e}")
            raise
    
    def stop(self):
        """Stop the MQTT client"""
        logger.info("Stopping MQTT Logger...")
        self.client.disconnect()
        self.client.loop_stop()

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received")
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start logger
    logger.info("=== Mouse Trap MQTT Logger Starting ===")
    mqtt_logger = MQTTLogger()
    mqtt_logger.start()
