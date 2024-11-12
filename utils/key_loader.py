from cryptography.fernet import Fernet
import json
import os

def load_api_keys():
    # Get the directory where key_loader.py is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load encryption key
    with open(os.path.join(current_dir, '.crypto_key'), 'rb') as key_file:
        key = key_file.read()
    
    f = Fernet(key)
    
    # Load encrypted keys
    with open(os.path.join(current_dir, '.encrypted_keys'), 'r') as file:
        encrypted_keys = json.load(file)
    
    # Decrypt keys
    decrypted_keys = {k: f.decrypt(v.encode()).decode() 
                     for k, v in encrypted_keys.items()}
    
    return decrypted_keys