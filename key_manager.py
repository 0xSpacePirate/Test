import configparser
from cryptography.fernet import Fernet
import os
import base64

CONFIG_FILE = 'config.ini'
ENCRYPTION_KEY_FILE = 'app.key'


def generate_key():
    """Generates an encryption key and saves it to a file."""
    key = Fernet.generate_key()
    with open(ENCRYPTION_KEY_FILE, 'wb') as key_file:
        key_file.write(key)
    return key


def load_key():
    """Loads the encryption key from a file, or generates it if it doesn't exist."""
    if not os.path.exists(ENCRYPTION_KEY_FILE):
        return generate_key()
    with open(ENCRYPTION_KEY_FILE, 'rb') as key_file:
        return key_file.read()


encryption_key = load_key()
fernet = Fernet(encryption_key)


def save_credentials(api_key, project_id):
    """Encrypts and saves BOTH the API key and Project ID."""
    if not api_key or not project_id:
        return

    config = configparser.ConfigParser()

    encrypted_key = fernet.encrypt(api_key.encode())
    encrypted_project_id = fernet.encrypt(project_id.encode())

    config['settings'] = {
        'openai_api_key': base64.b64encode(encrypted_key).decode('utf-8'),
        'openai_project_id': base64.b64encode(encrypted_project_id).decode('utf-8')
    }

    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def load_credentials():
    """Loads and decrypts BOTH the key and project ID. Returns a tuple (api_key, project_id)."""
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        if 'settings' in config and 'openai_api_key' in config['settings'] and 'openai_project_id' in config[
            'settings']:
            encrypted_key_b64 = config['settings']['openai_api_key']
            encrypted_key = base64.b64decode(encrypted_key_b64.encode('utf-8'))
            decrypted_key = fernet.decrypt(encrypted_key).decode()

            encrypted_project_id_b64 = config['settings']['openai_project_id']
            encrypted_project_id = base64.b64decode(encrypted_project_id_b64.encode('utf-8'))
            decrypted_project_id = fernet.decrypt(encrypted_project_id).decode()

            return decrypted_key, decrypted_project_id
    except Exception as e:
        print(f"Could not load or decrypt credentials: {e}")
        return None, None
    return None, None
