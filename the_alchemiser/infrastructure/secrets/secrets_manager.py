#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

AWS Secrets Manager Integration
Handles retrieving secrets from AWS Secrets Manager for the Quantitative Trading System.

Environment-Aware Behavior:
- Production (AWS Lambda): Only uses AWS Secrets Manager, fails hard if not available
- Development: Falls back to environment variables (including .env files) if AWS Secrets Manager fails
"""
from __future__ import annotations


import json
import logging
import os

try:
    import boto3
    from botocore.exceptions import ClientError

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logging.warning("boto3 not available - falling back to environment variables")


class SecretsManager:
    """Handles retrieving secrets from AWS Secrets Manager."""

    def __init__(self, region_name: str | None = None) -> None:
        """Initialize the Secrets Manager client.

        Args:
            region_name: AWS region where secrets are stored (if None, loads from config)

        """
        if region_name is None:
            from the_alchemiser.infrastructure.config import load_settings

            config = load_settings()
            region_name = config.secrets_manager.region_name
        self.region_name = region_name
        self.client = None
        self._secrets_cache: dict[str, str] | None = None  # Cache for secrets

        # Check if we're in production (AWS Lambda)
        self.is_production = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

        if BOTO3_AVAILABLE:
            try:
                self.client = boto3.client("secretsmanager", region_name=region_name)
                logging.debug(f"Initialized AWS Secrets Manager client for region: {region_name}")
            except Exception as e:
                if self.is_production:
                    # In production, AWS Secrets Manager must be available
                    logging.error(
                        f"CRITICAL: Failed to initialize AWS Secrets Manager client in production: {e}"
                    )
                    raise RuntimeError(
                        "AWS Secrets Manager is required in production environment"
                    ) from e
                logging.warning(f"Failed to initialize AWS Secrets Manager client: {e}")
                self.client = None
        else:
            if self.is_production:
                # In production, boto3 must be available
                logging.error("CRITICAL: boto3 not available in production environment")
                raise RuntimeError("boto3 is required in production environment")
            logging.info("boto3 not available - will use environment variables")

    def get_secret(self, secret_name: str) -> dict[str, str] | None:
        """Retrieve a secret from AWS Secrets Manager.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            Dictionary containing the secret values, or None if failed

        """
        # Use cache if available
        if self._secrets_cache is not None:
            return self._secrets_cache

        if not self.client:
            if self.is_production:
                # In production, we must have AWS Secrets Manager
                logging.error("CRITICAL: AWS Secrets Manager client not available in production")
                raise RuntimeError("AWS Secrets Manager is required in production environment")
            logging.warning(
                "AWS Secrets Manager client not available - falling back to environment variables"
            )
            self._secrets_cache = self._get_secret_from_env()
            return self._secrets_cache

        try:
            logging.debug(f"Retrieving secret: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_string = response["SecretString"]
            secret_dict = json.loads(secret_string)
            logging.debug(f"Successfully retrieved secret: {secret_name}")
            self._secrets_cache = secret_dict
            return self._secrets_cache
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logging.error(f"AWS Secrets Manager error ({error_code}): {e}")
            if error_code == "ResourceNotFoundException":
                logging.error(f"Secret '{secret_name}' not found in AWS Secrets Manager")
            elif error_code == "InvalidRequestException":
                logging.error(f"Invalid request for secret '{secret_name}'")
            elif error_code == "InvalidParameterException":
                logging.error(f"Invalid parameter for secret '{secret_name}'")
            elif error_code == "DecryptionFailureException":
                logging.error(f"Cannot decrypt secret '{secret_name}'")
            elif error_code == "InternalServiceErrorException":
                logging.error(f"Internal service error retrieving secret '{secret_name}'")

            if self.is_production:
                # In production, AWS Secrets Manager failure is fatal
                logging.error(
                    "CRITICAL: AWS Secrets Manager failed in production - not falling back"
                )
                raise RuntimeError(f"AWS Secrets Manager failed in production: {error_code}") from e
            logging.warning("Falling back to environment variables")
            self._secrets_cache = self._get_secret_from_env()
            return self._secrets_cache
        except Exception as e:
            logging.error(f"Unexpected error retrieving secret '{secret_name}': {e}")
            if self.is_production:
                # In production, any failure is fatal
                logging.error("CRITICAL: Unexpected error in AWS Secrets Manager in production")
                raise RuntimeError(f"AWS Secrets Manager failed in production: {e}") from e
            logging.warning("Falling back to environment variables")
            self._secrets_cache = self._get_secret_from_env()
            return self._secrets_cache

    def _get_secret_from_env(self) -> dict[str, str] | None:
        """Fallback method to get secrets from environment variables (development only).

        In production (Lambda), environment variables are set directly on the Lambda function.
        In development, environment variables can come from .env files loaded by pydantic.

        Returns:
            Dictionary containing the secret values from environment variables

        """
        if self.is_production:
            logging.warning(
                "Using environment variables in production - ensure Lambda env vars are set correctly"
            )
        else:
            logging.info(
                "Development mode: Loading secrets from environment variables (may include .env)"
            )

        secrets = {}

        # Try to get all the expected secrets from environment variables
        env_mappings = {
            "ALPACA_KEY": "ALPACA_KEY",
            "ALPACA_SECRET": "ALPACA_SECRET",
            "ALPACA_PAPER_KEY": "ALPACA_PAPER_KEY",
            "ALPACA_PAPER_SECRET": "ALPACA_PAPER_SECRET",
            "TWELVEDATA_KEY": "TWELVEDATA_KEY",
        }

        for key, env_var in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                secrets[key] = value
                if self.is_production:
                    logging.info(f"Loaded {key} from Lambda environment variable")
                else:
                    logging.info(f"Loaded {key} from environment variable (dev)")

        return secrets if secrets else None

    def get_alpaca_keys(self, paper_trading: bool = True) -> tuple[str, str] | tuple[None, None]:
        """Get Alpaca API keys for trading.

        Args:
            paper_trading: Whether to get paper trading keys or live keys

        Returns:
            Tuple of (api_key, secret_key) or (None, None) if not found

        """
        try:
            from the_alchemiser.infrastructure.config import load_settings

            config = load_settings()
            secret_name = config.secrets_manager.secret_name
            secrets = self.get_secret(secret_name)
            if not secrets:
                logging.error("No secrets found")
                return None, None

            if paper_trading:
                api_key = secrets.get("ALPACA_PAPER_KEY")
                secret_key = secrets.get("ALPACA_PAPER_SECRET")
                mode = "paper"
            else:
                api_key = secrets.get("ALPACA_KEY")
                secret_key = secrets.get("ALPACA_SECRET")
                mode = "live"

            if not api_key or not secret_key:
                logging.error(f"Missing Alpaca {mode} trading keys in secrets")
                return None, None

            logging.info(f"Successfully retrieved Alpaca {mode} trading keys")
            return api_key, secret_key

        except Exception as e:
            logging.error(f"Error getting Alpaca keys: {e}")
            return None, None

    def get_twelvedata_api_key(self) -> str | None:
        """Get TwelveData API key from secrets.

        Returns:
            API key string or None if not found

        """
        try:
            from the_alchemiser.infrastructure.config import load_settings

            config = load_settings()
            secret_name = config.secrets_manager.secret_name
            secrets = self.get_secret(secret_name)
            if not secrets:
                logging.error("No secrets found")
                return None

            api_key = secrets.get("TWELVEDATA_KEY")

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
