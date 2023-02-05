import yaml
import os

config_path = os.getenv('CONFIG_PATH', 'config.yml')
_config = yaml.safe_load(open(config_path, 'r'))

BOT_TOKEN = _config['bot']['token']
BOT_ENABLED_CHATS = _config['bot']['enabled_chats']

API_HOST = _config['enginetribe_api']['host']
API_KEY = _config['enginetribe_api']['api_key']
API_TOKEN = _config['enginetribe_api']['token']

WEBHOOK_HOST = _config['webhook']['host']
WEBHOOK_PORT = _config['webhook']['port']
