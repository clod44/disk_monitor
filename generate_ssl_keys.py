import os
import sys
import socket
import ipaddress
from datetime import datetime, timedelta

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from utils import get_base_path
from config_manager import ConfigManager

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
    try:
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        private_ip = get_local_ip()
        common_name = private_ip
        
        subject = issuer = x509.Name([
            x509.NameAttribute(x509.oid.NameOID.COUNTRY_NAME, u"TR"),
            x509.NameAttribute(x509.oid.NameOID.STATE_OR_PROVINCE_NAME, u"ISTANBUL"),
            x509.NameAttribute(x509.oid.NameOID.LOCALITY_NAME, u"Kadikoy"),
            x509.NameAttribute(x509.oid.NameOID.ORGANIZATION_NAME, u"Disk Monitor Project"),
            x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, common_name),
        ])
        
        san_ext = x509.SubjectAlternativeName([
            x509.DNSName(u"localhost"),
            x509.IPAddress(ipaddress.IPv4Address(u"127.0.0.1")),
            x509.IPAddress(ipaddress.IPv4Address(private_ip))
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            san_ext, critical=False,
        ).sign(key, hashes.SHA256(), default_backend())
        
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))
            
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
            
        print(f"Successfully generated '{cert_path}' and '{key_path}'.")

    except Exception as e:
        print(f"Error generating SSL keys: {e}")
        sys.exit(1)


if __name__ == '__main__':
    print("Running SSL key generation script...")
    cm = ConfigManager()
    generate_ssl_keys(cm)