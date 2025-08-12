import os
from datetime import datetime

class Logger:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        
        log_dir = os.path.dirname(log_file_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        try:
            with open(self.log_file_path, 'a') as f:
                pass
        except Exception as e:
            print(f"Error creating log file at {self.log_file_path}: {e}")

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        print(log_entry) 
        try:
            with open(self.log_file_path, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to log file: {e}")
