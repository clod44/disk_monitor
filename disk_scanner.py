import psutil
from datetime import datetime
from logger import Logger

def disk_stats(config_manager, logger):
    data = None
    disk_path = config_manager.get('DISK_MONITOR', 'disk_path')
    usage_threshold = config_manager.get('DISK_MONITOR', 'usage_threshold', int)

    try:
        disk_usage = psutil.disk_usage(disk_path)
        
        data = {
            'disk_path': disk_path,
            'usage_threshold': usage_threshold,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'disk_usage': {
                'total': round(disk_usage.total / (1024**3), 2),
                'used': round(disk_usage.used / (1024**3), 2),
                'free': round(disk_usage.free / (1024**3), 2),
                'percent': disk_usage.percent
            },
            'disk_status': 'OK' if disk_usage.percent < usage_threshold else 'WARNING',
            'check_interval_minutes': config_manager.get('DISK_MONITOR', 'check_interval_minutes', float)
        }
        
        report_message = (
            f"Disk Usage Report for '{disk_path}':\n"
            f"    Total: {data['disk_usage']['total']} GB\n"
            f"    Used: {data['disk_usage']['used']} GB\n"
            f"    Free: {data['disk_usage']['free']} GB\n"
            f"    Percent Used: {data['disk_usage']['percent']}% (!{usage_threshold})\n"
        )
        
        if data['disk_usage']['percent'] >= usage_threshold:
            report_message += f"    WARNING: Disk usage is above the {usage_threshold}% threshold!"

        logger.log(report_message, level="INFO")
            
    except Exception as e:
        logger.log(f"Error checking disk space: {e}", level="ERROR")
    
    return data

if __name__ == '__main__':
    from config_manager import ConfigManager
    config_manager = ConfigManager()
    disk_path = config_manager.get('DISK_MONITOR', 'disk_path')
    log_file_path = config_manager.get('DISK_MONITOR', 'log_file')
    usage_threshold = config_manager.get('DISK_MONITOR', 'usage_threshold', int)
    logger = Logger(log_file_path)

    print(f"Running disk space check...")
    stats = disk_stats(config_manager, logger)
    if stats:
        print(f"Stats returned: {stats}")