import os
import yaml

class Config:
    _instance = None
    
    def __new__(cls, config_path=None):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance
    
    def _load_config(self, config_path=None):
        if config_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            config_path = os.path.join(project_root, 'config.yaml')
        with open(config_path, 'r') as f:
            self._config = yaml.safe_load(f)

    def get(self, key, default=None):
        return self._config.get(key, default)

    def __getitem__(self, key):
        return self._config[key]

    def __contains__(self, key):
        return key in self._config

# Usage example:
# config = Config()
# log_path = config.get('log_path', 'logs/app.log')
