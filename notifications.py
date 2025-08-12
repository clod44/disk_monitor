import os
import json
from pywebpush import webpush, WebPushException
from config_manager import ConfigManager
from logger import Logger
from disk_scanner import disk_stats
import traceback

def send_notification(config_manager, logger, payload):
    VAPID_PUBLIC_KEY = config_manager.get('NOTIFICATIONS', 'vapid_public_key')
    VAPID_PRIVATE_KEY = config_manager.get('NOTIFICATIONS', 'vapid_private_key')
    VAPID_CLAIMS = { "sub": config_manager.get('NOTIFICATIONS', 'vapid_email') }
    subscription_file = config_manager.get('NOTIFICATIONS', 'subscription_file')
    
    if not os.path.exists(subscription_file) or os.path.getsize(subscription_file) == 0:
        return
    payload_str = json.dumps(payload)
    
    with open(subscription_file, 'r') as f:
        subscriptions = json.load(f)

    valid_subscriptions = []
    for subscription_info in subscriptions:
        try:
            webpush(
                subscription_info=subscription_info,
                data=payload_str, 
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            valid_subscriptions.append(subscription_info)
        except WebPushException as e:
            if e.response and e.response.status_code in [404, 410]:
                pass
            else:
                print(f"WebPushException: {e}")
                pass
    
    with open(subscription_file, 'w') as f:
        json.dump(valid_subscriptions, f)



def check_disk_warning(config_manager, logger, data):
    enable_notifications = config_manager.get('NOTIFICATIONS', 'enable_notifications', bool)

    if (data['disk_usage'] and data['disk_usage']['percent'] >= data['usage_threshold']):
        message = {
            "title": "PACS Disk Space Alert!",
            "body": f"Disk usage on '{data['disk_path']}' is at {data['disk_usage']['percent']}%. Contact Integration Team."
        }
        logger.log(f"Disk usage WARNING: {message['body']}", level="WARNING")
        if enable_notifications == False:
            return
        try:
            print("Trying to send notification...")
            send_notification(config_manager, logger, message)
            print("Successfully sent notification.")
        except Exception as e:
            logger.log("Failed to send notification due to an exception.", level="ERROR")
            traceback_str = traceback.format_exc()
            logger.log(f"Full Traceback:\n{traceback_str}", level="ERROR")







def save_subscription(config_manager, logger, subscription_info):
    subscription_file = config_manager.get('NOTIFICATIONS', 'subscription_file')
    subscriptions = []
    if os.path.exists(subscription_file) and os.path.getsize(subscription_file) > 0:
        with open(subscription_file, 'r') as f:
            subscriptions = json.load(f)
    if subscription_info not in subscriptions:
        subscriptions.append(subscription_info)
        with open(subscription_file, 'w') as f:
            json.dump(subscriptions, f)
        return True
    return False

    
def unsubscribe(config_manager, logger, endpoint):
    subscription_file = config_manager.get('NOTIFICATIONS', 'subscription_file')
    if not os.path.exists(subscription_file):
        return False
    
    with open(subscription_file, 'r') as f:
        try:
            subscriptions = json.load(f)
        except json.JSONDecodeError:
            subscriptions = []

    original_count = len(subscriptions)
    subscriptions = [sub for sub in subscriptions if sub.get('endpoint') != endpoint]

    if len(subscriptions) < original_count:
        with open(subscription_file, 'w') as f:
            json.dump(subscriptions, f, indent=2)
        return True
    
    return False