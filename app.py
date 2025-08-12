import os
import subprocess
import sys
import shutil
import socket
import json
import traceback
from flask import Flask, jsonify, request, render_template, send_file, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from config_manager import ConfigManager
from logger import Logger
from disk_scanner import disk_stats
from generate_ssl_keys import generate_ssl_keys
from generate_vapid_keys import generate_vapid_keys
from notifications import send_notification, check_disk_warning, save_subscription, unsubscribe
from service_manager import install_service_from_config

app = Flask(__name__)

config_manager = ConfigManager()

log_file_path = config_manager.get('DISK_MONITOR', 'log_file')
disk_path = config_manager.get('DISK_MONITOR', 'disk_path')
usage_threshold = config_manager.get('DISK_MONITOR', 'usage_threshold', int)
logger = Logger(log_file_path)
enable_notifications = config_manager.get('NOTIFICATIONS', 'enable_notifications', bool)
latest_disk_stats = {}

def log_config_on_startup():
    config_message = "Application configuration loaded:\n"
    for section in config_manager.settings:
        config_message += f"[{section}]\n"
        for key, value in config_manager.settings[section].items():
            config_message += f"{key} = {value}\n"
    logger.log(config_message, level="INFO")

def fetch_disk_stats():
    global latest_disk_stats
    stats = disk_stats(config_manager, logger)
    if stats:
        latest_disk_stats = stats
        check_disk_warning(config_manager, logger, latest_disk_stats)

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=fetch_disk_stats,
    trigger='interval',
    seconds=config_manager.get('DISK_MONITOR', 'check_interval_minutes', float) * 60,
    args=[]
)
scheduler.start()
fetch_disk_stats()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/disk_stats', methods=['GET'])
def get_disk_stats():
    global latest_disk_stats
    client_ip = request.remote_addr
    logger.log(f"disk_stats endpoint was accessed by {client_ip}.", level="INFO")
    return jsonify(latest_disk_stats)


@app.route('/vapid_public_key', methods=['GET'])
def get_vapid_public_key_route():
    key_file_path = config_manager.get('NOTIFICATIONS', 'vapid_public_key')
    try:
        with open(key_file_path, 'r') as f:
            vapid_public_key = f.read().strip()
        return jsonify({"vapid_public_key": vapid_public_key})
    except FileNotFoundError:
        return jsonify({"error": f"VAPID public key file not found at {key_file_path}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/subscribed_devices', methods=['GET'])
def get_subscriptions():
    subscription_file = config_manager.get('NOTIFICATIONS', 'subscription_file')
    try:
        content = ""
        with open(subscription_file, 'r') as f:
            content = f.read().strip()
        response = jsonify({"subscribed_devices": content})
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache' 
        response.headers['Expires'] = '0'
        return response
    except FileNotFoundError:
        return jsonify({"error": f"subscriptions file not found at {subscription_file}"}), 500
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500



@app.route('/subscribe', methods=['POST'])
def subscribe_endpoint():
    subscription_info = request.json
    if subscription_info is None:
        return jsonify({'message': 'Invalid JSON in request body.'}), 400
    success = save_subscription(config_manager,logger,subscription_info)
    if success:
        return jsonify({'message': 'Subscription added successfully.'})
    else:
        return jsonify({'message': 'Subscription already exists.'})




@app.route('/unsubscribe', methods=['POST'])
def post_unsubscribe():
    try:
        subscription_info = request.json
        if not subscription_info or 'endpoint' not in subscription_info:
            return jsonify({'message': 'Invalid request format. Expected a JSON body with an "endpoint" key.'}), 400
        endpoint = subscription_info['endpoint']
        success = unsubscribe(config_manager,logger,endpoint)
        if success:
            return jsonify({'message': 'Unsubscribed successfully.'}), 200
        else:
            return jsonify({'message': 'Subscription not found or already removed.'}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'message': 'An internal server error occurred.'}), 500



@app.route('/broadcast', methods=['POST'])
def post_broadcast():
    try:
        payload = request.json
        if not payload: #prevent double serialization
            return jsonify({'message': 'Invalid payload.'}), 400
        send_notification(config_manager, logger, payload)
        return jsonify({'message': 'Broadcast sent successfully.'})
    except Exception as e:
        print(f"Failed to broadcast notification: {e}")
        return jsonify({'message': f'Failed to send broadcast: {e}'}), 500


@app.route('/download-cert')
def download_certificate():
    ssl_cert_path = config_manager.get('WEB_SERVER', 'ssl_cert_path')
    if os.path.exists(ssl_cert_path):
        return send_file(ssl_cert_path, as_attachment=True)
    else:
        return "Certificate file not found.", 404

@app.route('/download-cert-installer')
def download_certificate_installer():
      return send_from_directory(app.static_folder, 'certificate-installer.7z', as_attachment=True)

if __name__ == '__main__':
    port = config_manager.get('WEB_SERVER', 'port', int)
    ssl_cert_path = config_manager.get('WEB_SERVER', 'ssl_cert_path')
    ssl_key_path = config_manager.get('WEB_SERVER', 'ssl_key_path')
    
    generate_vapid_keys(config_manager)
    
    ssl_context = None
    if ssl_cert_path and ssl_key_path:
        generate_ssl_keys(config_manager)
        if os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
            ssl_context = (ssl_cert_path, ssl_key_path)
    
    install_service_from_config(config_manager, logger, "app")

    if ssl_context:
        print("Server will run with Flask's development server over SSL. Access via HTTPS.")
        app.run(debug=True, use_reloader=False, host='0.0.0.0', port=port, ssl_context=ssl_context)
    else:
        print("No SSL configuration found or key generation failed. Running with Flask's simple server.")
        app.run(debug=True, use_reloader=False, host='0.0.0.0', port=port)
