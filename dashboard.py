#!/usr/bin/env python3
"""
Flask Web Dashboard for Mouse Trap Monitoring System
Real-time web interface with SocketIO for live updates
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import sqlite3
from datetime import datetime, timedelta
import json
import logging
import paho.mqtt.client as mqtt
from threading import Thread

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this'
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration
DATABASE_PATH = "/var/lib/trap-monitor/trap_events.db"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseHandler:
    """Handle database queries"""
    
    @staticmethod
    def get_connection():
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def get_all_nodes():
        """Get all node status information"""
        conn = DatabaseHandler.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT node_id, mac_address, last_seen, last_event_type,
                   total_triggers, battery_voltage, is_online
            FROM node_status
            ORDER BY node_id
        ''')
        nodes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return nodes
    
    @staticmethod
    def get_recent_events(limit=50):
        """Get recent trap events"""
        conn = DatabaseHandler.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, node_id, event_type, event_type_str, trap_count,
                   battery_voltage, route_hops, received_at
            FROM trap_events
            ORDER BY received_at DESC
            LIMIT ?
        ''', (limit,))
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return events
    
    @staticmethod
    def get_node_events(node_id, limit=20):
        """Get events for specific node"""
        conn = DatabaseHandler.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, node_id, event_type, event_type_str, trap_count,
                   battery_voltage, received_at
            FROM trap_events
            WHERE node_id = ?
            ORDER BY received_at DESC
            LIMIT ?
        ''', (node_id, limit))
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return events
    
    @staticmethod
    def get_statistics(days=7):
        """Get statistics for the past N days"""
        conn = DatabaseHandler.get_connection()
        cursor = conn.cursor()
        
        # Daily trigger counts
        cursor.execute('''
            SELECT date, total_triggers
            FROM statistics
            WHERE date >= date('now', '-' || ? || ' days')
            ORDER BY date
        ''', (days,))
        daily_stats = [dict(row) for row in cursor.fetchall()]
        
        # Total triggers
        cursor.execute('SELECT SUM(total_triggers) as total FROM statistics')
        total = cursor.fetchone()['total'] or 0
        
        # Active nodes
        cursor.execute('SELECT COUNT(*) as count FROM node_status WHERE is_online = 1')
        active_nodes = cursor.fetchone()['count']
        
        # Triggers in last 24 hours
        cursor.execute('''
            SELECT COUNT(*) as count FROM trap_events
            WHERE event_type = 1 AND received_at >= datetime('now', '-1 day')
        ''')
        last_24h = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            'daily': daily_stats,
            'total_triggers': total,
            'active_nodes': active_nodes,
            'triggers_24h': last_24h
        }
    
    @staticmethod
    def get_battery_status():
        """Get battery status for all nodes"""
        conn = DatabaseHandler.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT node_id, battery_voltage, last_seen
            FROM node_status
            ORDER BY battery_voltage ASC
        ''')
        batteries = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return batteries

# MQTT Client for live updates
class MQTTSubscriber:
    """Subscribe to MQTT and forward to SocketIO"""
    
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT connected for live updates")
            client.subscribe("trap/#")
    
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            # Forward to all connected WebSocket clients
            socketio.emit('trap_event', payload, namespace='/')
            logger.info(f"Live event forwarded: Node {payload.get('node_id')}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def start(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            logger.info("MQTT subscriber started")
        except Exception as e:
            logger.error(f"Error starting MQTT subscriber: {e}")

# Start MQTT subscriber in background
mqtt_subscriber = MQTTSubscriber()
mqtt_subscriber.start()

# ==================== WEB ROUTES ====================

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/nodes')
def api_nodes():
    """Get all node status"""
    try:
        nodes = DatabaseHandler.get_all_nodes()
        return jsonify({'success': True, 'nodes': nodes})
    except Exception as e:
        logger.error(f"Error getting nodes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/events')
def api_events():
    """Get recent events"""
    try:
        limit = request.args.get('limit', 50, type=int)
        events = DatabaseHandler.get_recent_events(limit)
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        logger.error(f"Error getting events: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/node/<int:node_id>/events')
def api_node_events(node_id):
    """Get events for specific node"""
    try:
        limit = request.args.get('limit', 20, type=int)
        events = DatabaseHandler.get_node_events(node_id, limit)
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        logger.error(f"Error getting node events: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/statistics')
def api_statistics():
    """Get system statistics"""
    try:
        days = request.args.get('days', 7, type=int)
        stats = DatabaseHandler.get_statistics(days)
        return jsonify({'success': True, 'statistics': stats})
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/battery')
def api_battery():
    """Get battery status for all nodes"""
    try:
        batteries = DatabaseHandler.get_battery_status()
        return jsonify({'success': True, 'batteries': batteries})
    except Exception as e:
        logger.error(f"Error getting battery status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== SOCKETIO EVENTS ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('request_update')
def handle_update_request():
    """Handle client request for data update"""
    try:
        nodes = DatabaseHandler.get_all_nodes()
        events = DatabaseHandler.get_recent_events(20)
        stats = DatabaseHandler.get_statistics(7)
        
        emit('data_update', {
            'nodes': nodes,
            'events': events,
            'statistics': stats
        })
    except Exception as e:
        logger.error(f"Error handling update request: {e}")

if __name__ == '__main__':
    logger.info("=== Flask Dashboard Starting ===")
    logger.info("Access dashboard at: http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
