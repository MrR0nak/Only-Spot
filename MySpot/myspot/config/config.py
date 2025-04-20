import os
import json
import logging
from pathlib import Path
logger = logging.getLogger(__name__)
class ConfigManager:
    DEFAULT_CONFIG = {
        'music_directory': str(Path.home() / 'Music'),
        'volume': 0.5,
        'last_played': None,
        'theme': 'dark'
    }
    def __init__(self, config_file='settings.json'):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(base_dir, 'config', config_file)
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
    def load_config(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.info(f"No configuration file found at {self.config_path}, using defaults")
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    def save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    def get(self, key, default=None):
        return self.config.get(key, default)
    def set(self, key, value):
        self.config[key] = value
        return self.save_config()
    def update(self, config_dict):
        self.config.update(config_dict)
        return self.save_config()