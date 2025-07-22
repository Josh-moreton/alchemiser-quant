import os
import yaml

class Config:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
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
