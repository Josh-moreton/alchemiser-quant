import os
import yaml
import logging

class Config:
    """Singleton configuration class that loads config.yaml once and shares it across the application."""
    _instance = None
    _initialized = False
    
    def __new__(cls, config_path=None):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_path=None):
        # Only initialize once, even if __init__ is called multiple times
        if not Config._initialized:
            self._load_config(config_path)
            Config._initialized = True
    
    def _load_config(self, config_path=None):
        """Load configuration from YAML file."""
        if config_path is None:
            # Look for config.yaml in the_alchemiser directory (parent of core)
            the_alchemiser_root = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(the_alchemiser_root, 'config.yaml')
        
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            logging.info(f"Configuration loaded from {config_path}")
        except FileNotFoundError:
            logging.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML configuration: {e}")
            raise

    def get(self, key, default=None):
        """Get configuration value with optional default."""
        return self._config.get(key, default)

    def __getitem__(self, key):
        """Dictionary-style access to configuration."""
        return self._config[key]

    def __contains__(self, key):
        """Check if key exists in configuration."""
        return key in self._config
    
    def reload(self, config_path=None):
        """Reload configuration (useful for testing)."""
        Config._initialized = False
        self._load_config(config_path)
        Config._initialized = True

# Global config instance - load once and reuse
_global_config = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

# Usage example:
# config = Config()
# log_path = config.get('log_path', 'logs/app.log')
