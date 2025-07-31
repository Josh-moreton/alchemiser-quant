#!/usr/bin/env python3
"""
AWS Secrets Manager Integration
Handles retrieving secrets from AWS Secrets Manager for the Nuclear Trading Bot
"""

import json
import logging
import os
from typing import Dict, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logging.warning("boto3 not available - falling back to environment variables")

class SecretsManager:
    """Handles retrieving secrets from AWS Secrets Manager"""
    
    def __init__(self, region_name: Optional[str] = None):
        """
        Initialize the Secrets Manager client
        
        Args:
            region_name: AWS region where secrets are stored (if None, loads from config)
        """
        if region_name is None:
            from the_alchemiser.core.config import get_config
            config = get_config()
            region_name = config['secrets_manager'].get('region_name', 'eu-west-2')
        self.region_name = region_name
        self.client = None
        self._secrets_cache = None  # Cache for secrets
        
        if BOTO3_AVAILABLE:
            try:
                self.client = boto3.client('secretsmanager', region_name=region_name)
                logging.debug(f"Initialized AWS Secrets Manager client for region: {region_name}")
            except Exception as e:
                logging.warning(f"Failed to initialize AWS Secrets Manager client: {e}")
                self.client = None
        else:
            logging.info("boto3 not available - will use environment variables")
    
    def get_secret(self, secret_name: str) -> Optional[Dict]:
        """
        Retrieve a secret from AWS Secrets Manager
        
        Args:
            secret_name: Name of the secret to retrieve
            
        Returns:
            Dictionary containing the secret values, or None if failed
        """
        # Use cache if available
        if self._secrets_cache is not None:
            return self._secrets_cache
        if not self.client:
            logging.warning("AWS Secrets Manager client not available - falling back to environment variables")
            self._secrets_cache = self._get_secret_from_env()
            return self._secrets_cache
        try:
            logging.debug(f"Retrieving secret: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_string = response['SecretString']
            secret_dict = json.loads(secret_string)
            logging.debug(f"Successfully retrieved secret: {secret_name}")
            self._secrets_cache = secret_dict
            return self._secrets_cache
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logging.error(f"AWS Secrets Manager error ({error_code}): {e}")
            if error_code == 'ResourceNotFoundException':
                logging.error(f"Secret '{secret_name}' not found in AWS Secrets Manager")
            elif error_code == 'InvalidRequestException':
                logging.error(f"Invalid request for secret '{secret_name}'")
            elif error_code == 'InvalidParameterException':
                logging.error(f"Invalid parameter for secret '{secret_name}'")
            elif error_code == 'DecryptionFailureException':
                logging.error(f"Cannot decrypt secret '{secret_name}'")
            elif error_code == 'InternalServiceErrorException':
                logging.error(f"Internal service error retrieving secret '{secret_name}'")
            logging.warning("Falling back to environment variables")
            self._secrets_cache = self._get_secret_from_env()
            return self._secrets_cache
        except Exception as e:
            logging.error(f"Unexpected error retrieving secret '{secret_name}': {e}")
            logging.warning("Falling back to environment variables")
            self._secrets_cache = self._get_secret_from_env()
            return self._secrets_cache
    
    def _get_secret_from_env(self) -> Optional[Dict]:
        """
        Fallback method to get secrets from environment variables
        
        Returns:
            Dictionary containing the secret values from environment variables
        """
        secrets = {}
        
        # Try to get all the expected secrets from environment variables
        env_mappings = {
            'ALPACA_KEY': 'ALPACA_KEY',
            'ALPACA_SECRET': 'ALPACA_SECRET',
            'ALPACA_PAPER_KEY': 'ALPACA_PAPER_KEY',
            'ALPACA_PAPER_SECRET': 'ALPACA_PAPER_SECRET',
            'TELEGRAM_TOKEN': 'TELEGRAM_TOKEN',
            'TELEGRAM_CHAT_ID': 'TELEGRAM_CHAT_ID',
            'TWELVEDATA_KEY': 'TWELVEDATA_KEY'
        }
        
        for key, env_var in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                secrets[key] = value
                logging.info(f"Loaded {key} from environment variable")
        
        return secrets if secrets else None
    
    def get_alpaca_keys(self, paper_trading: bool = True) -> tuple:
        """
        Get Alpaca API keys for trading
        
        Args:
            paper_trading: Whether to get paper trading keys or live keys
            
        Returns:
            Tuple of (api_key, secret_key) or (None, None) if not found
        """
        try:
            from the_alchemiser.core.config import get_config
            config = get_config()
            secret_name = config['secrets_manager'].get('secret_name', 'nuclear-secrets')
            secrets = self.get_secret(secret_name)
            if not secrets:
                logging.error("No secrets found")
                return None, None
            
            if paper_trading:
                api_key = secrets.get('ALPACA_PAPER_KEY')
                secret_key = secrets.get('ALPACA_PAPER_SECRET')
                mode = "paper"
            else:
                api_key = secrets.get('ALPACA_KEY')
                secret_key = secrets.get('ALPACA_SECRET')
                mode = "live"
            
            if not api_key or not secret_key:
                logging.error(f"Missing Alpaca {mode} trading keys in secrets")
                return None, None
            
            logging.info(f"Successfully retrieved Alpaca {mode} trading keys")
            return api_key, secret_key
            
        except Exception as e:
            logging.error(f"Error getting Alpaca keys: {e}")
            return None, None
    
    def get_telegram_config(self) -> tuple:
        """
        Get Telegram bot configuration
        
        Returns:
            Tuple of (token, chat_id) or (None, None) if not found
        """
        try:
            from the_alchemiser.core.config import get_config
            config = get_config()
            secret_name = config['secrets_manager'].get('secret_name', 'nuclear-secrets')
            secrets = self.get_secret(secret_name)
            if not secrets:
                logging.error("No secrets found")
                return None, None
            
            token = secrets.get('TELEGRAM_TOKEN')
            chat_id = secrets.get('TELEGRAM_CHAT_ID')
            
            if not token or not chat_id:
                logging.error("Missing Telegram configuration in secrets")
                return None, None
            
            logging.info("Successfully retrieved Telegram configuration")
            return token, chat_id
            
        except Exception as e:
            logging.error(f"Error getting Telegram config: {e}")
            return None, None

    def get_twelvedata_api_key(self) -> Optional[str]:
        """
        Get TwelveData API key from secrets
        
        Returns:
            API key string or None if not found
        """
        try:
            from the_alchemiser.core.config import get_config
            config = get_config()
            secret_name = config['secrets_manager'].get('secret_name', 'nuclear-secrets')
            secrets = self.get_secret(secret_name)
            if not secrets:
                logging.error("No secrets found")
                return None
            
            api_key = secrets.get('TWELVEDATA_KEY')
            
            if not api_key:
                logging.error("Missing TwelveData API key (TWELVEDATA_KEY) in secrets")
                return None
            
            logging.info("Successfully retrieved TwelveData API key")
            return api_key
            
        except Exception as e:
            logging.error(f"Error getting TwelveData API key: {e}")
            return None


# Global instance for easy access
secrets_manager = SecretsManager()
