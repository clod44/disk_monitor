import os
import subprocess
import socket
import shutil
import sys

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def generate_ssl_keys(config_manager):
    cert_path = config_manager.get('WEB_SERVER', 'ssl_cert_path')
    key_path = config_manager.get('WEB_SERVER', 'ssl_key_path')

    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("SSL certificate and key files already exist. Skipping generation.")
        return

    print("Generating a new self-signed SSL certificate and key...")

    openssl_path = shutil.which('openssl')
    if not openssl_path:
        print("Error: 'openssl' command not found. Please install openssl to generate keys.")
        sys.exit(1)

    private_ip = get_local_ip()
    common_name = private_ip
    temp_cnf_path = 'openssl.cnf'
    
    try:
        with open(temp_cnf_path, 'w') as f:
            f.write("[req]\n")
            f.write("distinguished_name = req_distinguished_name\n")
            f.write("x509_extensions = v3_req\n")
            f.write("prompt = no\n")
            f.write("\n")
            f.write("[req_distinguished_name]\n")
            f.write("C = TR\n")
            f.write("ST = ISTANBUL\n")
            f.write("L = Kadikoy\n")
            f.write("O = Disk Monitor Project\n")
            f.write(f"CN = {common_name}\n")
            f.write("\n")
            f.write("[v3_req]\n")
            f.write("keyUsage = nonRepudiation, digitalSignature, keyEncipherment\n")
            f.write("extendedKeyUsage = serverAuth\n")
            f.write(f"subjectAltName = DNS:localhost, IP:127.0.0.1, IP:{private_ip}\n")
            f.write("\n")

        command = [
            openssl_path, 'req', '-x509', '-nodes', '-days', '365', 
            '-newkey', 'rsa:2048', '-keyout', key_path, 
            '-out', cert_path, 
            '-config', temp_cnf_path
        ]
        
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Successfully generated '{cert_path}' and '{key_path}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error generating SSL keys: {e}")
        sys.exit(1)
    finally:
        if os.path.exists(temp_cnf_path):
            os.remove(temp_cnf_path)

if __name__ == '__main__':
    print("Running SSL key generation script...")
    cm = ConfigManager()
    generate_ssl_keys(cm)