import os
import sys
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

def generate_vapid_keys(config_manager):
    public_key_path = config_manager.get('NOTIFICATIONS', 'vapid_public_key')
    private_key_path = config_manager.get('NOTIFICATIONS', 'vapid_private_key')

    if os.path.exists(public_key_path) and os.path.exists(private_key_path):
        print("VAPID key files already exist. Skipping generation.")
        return

    print("Generating new VAPID keys...")
    
    try:
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )

        vapid_public_key = base64.urlsafe_b64encode(public_bytes).rstrip(b'=').decode('utf-8')

    except Exception as e:
        print(f"Error: Failed to generate VAPID keys. Check cryptography library. Error: {e}")
        sys.exit(1)

    try:
        with open(public_key_path, 'w') as f:
            f.write(vapid_public_key)
        
        with open(private_key_path, 'w') as f:
            f.write(private_pem.decode('utf-8'))
            
        print(f"New VAPID keys have been generated and saved to '{public_key_path}' and '{private_key_path}'.")
        print("VAPID Public Key: ", vapid_public_key)
    except Exception as e:
        print(f"Error saving VAPID keys to files: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("Running VAPID key generation script...")
    cm = ConfigManager()
    generate_vapid_keys(cm)