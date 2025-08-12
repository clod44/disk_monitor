import os
import configparser

# Import the helper functions for path management
from utils import  get_base_path, get_resource_path

class ConfigManager:
    def __init__(self, config_file='config.ini'):
        base_dir = get_base_path()
        self.config_file = os.path.join(base_dir, config_file)
        
        self.config = configparser.ConfigParser()
        self._default_config = {
            'WEB_SERVER': {
                'port': '6161',
                'ssl_cert_path': 'cert.pem', 
                'ssl_key_path': 'key.pem',
            },
            'DISK_MONITOR': {
                'disk_path': '/',
                'log_file': 'disk_monitor.log',
                'usage_threshold': '50',
                'check_interval_minutes': '5',
            },
            'NOTIFICATIONS': {
                'enable_notifications': 'True',
                'vapid_public_key': 'vapid_public_key.txt',
                'vapid_private_key': 'vapid_private_key.pem',
                'vapid_email': 'mailto:your.email@example.com',
                'subscription_file': 'subscriptions.json',
            },
        }
        self.generate_config()
        self.read_config()

    def _strtobool_custom(self, value):
        if isinstance(value, str):
            value = value.lower()
            if value in ('y', 'yes', 't', 'true', 'on', '1'):
                return True
            if value in ('n', 'no', 'f', 'false', 'off', '0'):
                return False
        return False
        
    def generate_config(self):
        updated = False
        if not os.path.exists(self.config_file):
            print(f"Configuration file '{self.config_file}' not found. Generating a new one with default values.")
            for section, settings in self._default_config.items():
                self.config[section] = settings
            updated = True
        else:
            self.config.read(self.config_file)
            for section, settings in self._default_config.items():
                if section not in self.config:
                    self.config[section] = {}
                    updated = True
                for key, value in settings.items():
                    if key not in self.config[section]:
                        self.config[section][key] = value
                        updated = True
        if updated:
            self.write_config()
            print(f"Configuration file '{self.config_file}' is up-to-date.")

    def read_config(self):
        self.config.read(self.config_file)
        self.settings = {}
        for section in self.config.sections():
            self.settings[section] = dict(self.config.items(section))
        print("Configuration settings loaded.")

    def write_config(self):
        try:
            config_dir = os.path.dirname(self.config_file)
            if config_dir:
                os.makedirs(config_dir, exist_ok=True)
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            print(f"Configuration file '{self.config_file}' has been updated.")
        except IOError as e:
            print(f"Error writing to configuration file '{self.config_file}': {e}")
            
    def get(self, section, key, cast_as=str):
        value = self.settings.get(section, {}).get(key)        
        if value is None:
            return None
        # Automatically construct a full path for file-related settings
        if key.endswith('_path') or key.endswith('_file'):
            base_dir = get_base_path()
            return os.path.join(base_dir, value)
        try:
            if cast_as is bool:
                return self._strtobool_custom(value)
            return cast_as(value)
        except (ValueError, TypeError) as e:
            print(f"Error casting value '{value}' to type '{cast_as.__name__}': {e}")
            return None