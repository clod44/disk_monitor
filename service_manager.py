from utils import get_base_path, get_resource_path
import os
import subprocess
import configparser


def install_service_from_config(config_manager, logger, main_executable_name="app"):
    config = config_manager.config
    service_name = config['SERVICE']['service_name']
    service_file_path = f'/etc/systemd/system/{service_name}'    
    base_path = get_base_path()
    executable_path = os.path.join(base_path, main_executable_name)
    service_user = config['SERVICE']['user']
    service_group = config['SERVICE']['group']
    runtime_log_file = os.path.join(base_path, config['SERVICE']['runtime_log_file'])

    logger.log(f"Installing service: {service_name}", level="INFO")

    log_dir = os.path.dirname(runtime_log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    service_content = f"""
[Unit]
Description=Disk Monitor Service
After=network.target

[Service]
Type=simple
User={service_user}
Group={service_group}
ExecStart={executable_path}
WorkingDirectory={base_path}
Restart=always
StandardOutput=file:{runtime_log_file}
StandardError=file:{runtime_log_file}

[Install]
WantedBy=multi-user.target
"""
    try:
        logger.log(f"Stopping and disabling service: {service_name}", level="INFO")
        subprocess.run(['sudo', 'systemctl', 'stop', service_name], check=False, capture_output=True, text=True)
        subprocess.run(['sudo', 'systemctl', 'disable', service_name], check=False, capture_output=True, text=True)
        logger.log(f"Writing service file to {service_file_path}", level="INFO")
        p = subprocess.run(
            ['sudo', 'tee', service_file_path],
            input=service_content,
            check=True,
            text=True,
            capture_output=True
        )
        logger.log(f"Service file written successfully: {p.stdout}", level="INFO")

        logger.log("Reloading systemd daemon", level="INFO")
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True, capture_output=True, text=True)
        
        logger.log(f"Enabling service: {service_name}", level="INFO")
        subprocess.run(['sudo', 'systemctl', 'enable', service_name], check=True, capture_output=True, text=True)
        
        logger.log(f"Service {service_name} installed. use -sudo service disk_monitor start- to start it. service will not work of development version. runtime.log is only available with service mode", level="INFO")
    except subprocess.CalledProcessError as e:
        logger.log(f"Error during service installation: {e}", level="ERROR")
        logger.log(f"Stderr: {e.stderr}", level="ERROR")
        logger.log(f"Stdout: {e.stdout}", level="ERROR")
    except Exception as e:
        logger.log(f"Unexpected error during service installation: {e}", level="ERROR")