"""Configuration management for The Alchemiser Trading Bot.

This module provides a singleton configuration class that loads settings from
a YAML configuration file and makes them available throughout the application.
It implements the singleton pattern to ensure configuration is loaded only once
and shared across all modules.

The configuration system supports:
- YAML-based configuration files
- Default fallback values for missing sections
- Thread-safe singleton implementation
- Configuration reloading for testing
- Dictionary-style and method-based access

Example:
    Basic usage:
    
    >>> config = get_config()
    >>> log_level = config.get('logging', {}).get('level', 'INFO')
    >>> alpaca_config = config['alpaca']
"""

import os
import yaml
import logging


class Config:
    """Singleton configuration manager for the trading bot.
    
    This class implements the singleton pattern to ensure that configuration
    is loaded only once from the YAML file and shared across the entire
    application. It provides sensible defaults for missing configuration
    sections to ensure the application can run even with minimal configuration.
    
    Attributes:
        _instance (Config): The singleton instance
        _initialized (bool): Flag to track if configuration has been loaded
        _config (dict): The loaded configuration data
        
    Example:
        >>> config = Config()
        >>> alpaca_endpoint = config.get('alpaca', {}).get('endpoint')
        >>> log_level = config['logging']['level']
    """
    _instance = None
    _initialized = False
    
    def __new__(cls, config_path=None):
        """Create or return the singleton instance.
        
        Args:
            config_path (str, optional): Path to configuration file.
                Defaults to None (auto-detect).
                
        Returns:
            Config: The singleton configuration instance.
        """
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, config_path=None):
        """Initialize the configuration singleton.
        
        Only initializes once, even if __init__ is called multiple times
        due to the singleton pattern.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                If None, automatically looks for config.yaml in the package root.
        """
        # Only initialize once, even if __init__ is called multiple times
        if not Config._initialized:
            self._load_config(config_path)
            Config._initialized = True

    def _load_config(self, config_path=None):
        """Load configuration from YAML file with error handling.
        
        Args:
            config_path (str, optional): Path to configuration file.
                If None, looks for config.yaml in the package root directory.
                
        Raises:
            yaml.YAMLError: If the YAML file contains syntax errors.
            
        Note:
            If the configuration file is not found, an empty configuration
            is used and defaults will be provided by the get() method.
        """
        if config_path is None:
            # Look for config.yaml in the_alchemiser directory (parent of core)
            the_alchemiser_root = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(the_alchemiser_root, 'config.yaml')
        
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            logging.info(f"Configuration loaded from {config_path}")
        except FileNotFoundError:
            logging.warning(f"Configuration file not found: {config_path}, using defaults")
            self._config = {}
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML configuration: {e}")
            raise

    def get(self, key, default=None):
        """Get configuration value with intelligent defaults.
        
        Provides sensible default values for known configuration sections
        if they are missing from the configuration file. This ensures
        the application can run with minimal configuration.
        
        Args:
            key (str): Configuration key to retrieve.
            default (Any, optional): Default value if key is not found.
                Defaults to None.
                
        Returns:
            Any: The configuration value or default.
            
        Example:
            >>> config = Config()
            >>> alpaca_config = config.get('alpaca')
            >>> log_level = config.get('logging', {}).get('level', 'INFO')
        """
        # If top-level key is missing, provide sensible defaults for known sections
        if key not in self._config:
            # Sensible defaults for new config sections
            if key == 'aws':
                return {
                    'region': 'eu-west-2',
                    'account_id': '',
                    'repo_name': '',
                    'lambda_arn': '',
                    'image_tag': 'latest',
                }
            if key == 'alpaca':
                return {
                    'endpoint': 'https://api.alpaca.markets',
                    'paper_endpoint': 'https://paper-api.alpaca.markets/v2',
                    'cash_reserve_pct': 0.05,
                    'slippage_bps': 5,
                }
            if key == 'logging':
                return {
                    'level': 'INFO',
                }
            if key == 'alerts':
                return {
                    'alert_config_s3': '',
                    'cooldown_minutes': 30,
                }
            if key == 'secrets_manager':
                return {
                    'region_name': 'eu-west-2',
                    'secret_name': 'nuclear-secrets',
                }
            if key == 'strategy':
                return {
                    'default_strategy_allocations': {'nuclear': 0.5, 'tecl': 0.5},
                    'poll_timeout': 30,
                    'poll_interval': 2.0,
                }
            if key == 'email':
                return {
                    'smtp_server': 'smtp.mail.me.com',
                    'smtp_port': 587,
                    'from_email': None,  # Must be configured in config.yaml
                    'to_email': None,    # Must be configured in config.yaml
                    # smtp_password is stored in AWS Secrets Manager
                }
        return self._config.get(key, default)

    def __getitem__(self, key):
        """Dictionary-style access to configuration.
        
        Args:
            key (str): Configuration key to retrieve.
            
        Returns:
            Any: The configuration value.
            
        Raises:
            KeyError: If the key is not found in the configuration.
            
        Example:
            >>> config = Config()
            >>> alpaca_config = config['alpaca']
        """
        return self._config[key]

    def __contains__(self, key):
        """Check if key exists in configuration.
        
        Args:
            key (str): Configuration key to check.
            
        Returns:
            bool: True if key exists, False otherwise.
            
        Example:
            >>> config = Config()
            >>> if 'alpaca' in config:
            ...     print("Alpaca configuration found")
        """
        return key in self._config
    
    def reload(self, config_path=None):
        """Reload configuration from file.
        
        Useful for testing scenarios where configuration needs to be
        changed during runtime.
        
        Args:
            config_path (str, optional): Path to configuration file.
                If None, uses the original path or auto-detection.
                
        Note:
            This method resets the singleton initialization state and
            reloads the configuration from the specified file.
        """
        Config._initialized = False
        self._load_config(config_path)
        Config._initialized = True


# Global config instance - load once and reuse
_global_config = None


def get_config() -> Config:
    """Get the global configuration instance.
    
    This function provides access to the singleton configuration instance.
    The configuration is loaded once when first accessed and reused
    throughout the application lifecycle.
    
    Returns:
        Config: The singleton configuration instance.
        
    Example:
        >>> config = get_config()
        >>> alpaca_config = config.get('alpaca')
        >>> if 'logging' in config:
        ...     log_level = config['logging']['level']
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config
