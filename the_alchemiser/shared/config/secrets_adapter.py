#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Simple environment-based secrets helper with automatic detection.

This module provides a simple approach for loading secrets:
- Local development: Loads from environment variables (.env file)
- AWS Lambda: Loads from AWS Secrets Manager
- Trading mode determined by which credentials you store where
"""

from __future__ import annotations

import json
import logging
import os

# Auto-load .env file into environment variables
from the_alchemiser.shared.config import env_loader  # noqa: F401
from the_alchemiser.shared.config.config import load_settings

logger = logging.getLogger(__name__)

# Try to import boto3 for AWS Secrets Manager support
try:
    import boto3
    from botocore.exceptions import ClientError

    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not available - falling back to environment variables only")


def get_alpaca_keys() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca API keys from the appropriate source.

    Simple environment detection:
    - If AWS_LAMBDA_FUNCTION_NAME exists: Use AWS Secrets Manager
    - Otherwise: Use environment variables (.env file)

    Returns:
        Tuple of (api_key, secret_key, endpoint) or (None, None, None) if not found

    """
    # Simple environment detection
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # In Lambda - get from AWS Secrets Manager
        logger.info("Detected AWS Lambda environment - loading from Secrets Manager")
        return _get_alpaca_keys_from_aws()
    # Local dev - get from .env
    logger.info("Detected local environment - loading from environment variables")
    return _get_alpaca_keys_from_env()


def _get_alpaca_keys_from_aws() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca keys from AWS Secrets Manager."""
    if not BOTO3_AVAILABLE:
        logger.error("boto3 not available for AWS Secrets Manager access")
        return None, None, None

    try:
        # Initialize AWS Secrets Manager client
        client = boto3.client("secretsmanager", region_name="eu-west-2")

        # Get the secret
        response = client.get_secret_value(SecretId="the-alchemiser-secrets")
        secret_data = json.loads(response["SecretString"])

        api_key = secret_data.get("ALPACA_KEY")
        secret_key = secret_data.get("ALPACA_SECRET")
        endpoint = secret_data.get("ALPACA_ENDPOINT")

        # Require at least API key and secret key
        if not api_key or not secret_key:
            logger.error(
                "Missing required Alpaca credentials in AWS Secrets Manager: ALPACA_KEY, ALPACA_SECRET"
            )
            return None, None, None

        # If no endpoint specified, default to paper trading
        if not endpoint:
            endpoint = "https://paper-api.alpaca.markets"
            logger.info(
                "No ALPACA_ENDPOINT in AWS Secrets Manager, defaulting to paper trading mode"
            )

        logger.info("Successfully loaded Alpaca credentials from AWS Secrets Manager")
        return api_key, secret_key, endpoint

    except ClientError as e:
        logger.error(f"Failed to retrieve secrets from AWS: {e}")
        return None, None, None
    except Exception as e:
        logger.error(f"Unexpected error retrieving AWS secrets: {e}")
        return None, None, None


def _get_alpaca_keys_from_env() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca keys from environment variables (.env file auto-loaded)."""
    # Try both formats: ALPACA_KEY and ALPACA__KEY (Pydantic nested format)
    api_key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA__KEY")
    secret_key = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA__SECRET")
    endpoint = os.getenv("ALPACA_ENDPOINT") or os.getenv("ALPACA__ENDPOINT")

    # Require at least API key and secret key
    if not api_key or not secret_key:
        logger.error(
            "Missing required Alpaca credentials in environment variables: ALPACA_KEY/ALPACA__KEY, ALPACA_SECRET/ALPACA__SECRET"
        )
        return None, None, None

    # If no endpoint specified, default to paper trading
    if not endpoint:
        endpoint = "https://paper-api.alpaca.markets"
        logger.info("No ALPACA_ENDPOINT specified, defaulting to paper trading mode")

    logger.info("Successfully loaded Alpaca credentials from environment variables")
    return api_key, secret_key, endpoint


def get_twelvedata_api_key() -> str | None:
    """Get TwelveData API key from the appropriate source."""
    # Simple environment detection
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # In Lambda - get from AWS Secrets Manager
        logger.info("Detected AWS Lambda environment - loading TwelveData key from Secrets Manager")
        return _get_twelvedata_key_from_aws()
    # Local dev - get from .env
    logger.info("Detected local environment - loading TwelveData key from environment variables")
    return _get_twelvedata_key_from_env()


def _get_twelvedata_key_from_aws() -> str | None:
    """Get TwelveData key from AWS Secrets Manager."""
    if not BOTO3_AVAILABLE:
        logger.error("boto3 not available for AWS Secrets Manager access")
        return None

    try:
        client = boto3.client("secretsmanager", region_name="eu-west-2")
        response = client.get_secret_value(SecretId="the-alchemiser-secrets")
        secret_data = json.loads(response["SecretString"])

        api_key = secret_data.get("TWELVEDATA_KEY")
        if not api_key:
            logger.warning("TwelveData API key not found in AWS Secrets Manager")
            return None

        logger.info("Successfully loaded TwelveData API key from AWS Secrets Manager")
        return str(api_key)

    except ClientError as e:
        logger.error(f"Failed to retrieve TwelveData key from AWS: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving TwelveData key from AWS: {e}")
        return None


def _get_twelvedata_key_from_env() -> str | None:
    """Get TwelveData key from environment variables."""
    api_key = os.getenv("TWELVEDATA_KEY")

    if not api_key:
        logger.warning("TwelveData API key not found in environment variables")
        return None

    logger.info("Successfully loaded TwelveData API key from environment")
    return api_key


def get_email_password() -> str | None:
    """Get email password from the appropriate source.

    Simple environment detection:
    - If AWS_LAMBDA_FUNCTION_NAME exists: Use AWS Secrets Manager
    - Otherwise: Use environment variables (.env file)

    Returns:
        Email password string or None if not found

    """
    # Simple environment detection
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # In Lambda - get from AWS Secrets Manager
        logger.info("Detected AWS Lambda environment - loading email password from Secrets Manager")
        return _get_email_password_from_aws()
    # Local dev - get from .env
    logger.info("Detected local environment - loading email password from environment variables")
    return _get_email_password_from_env()


def _get_email_password_from_aws() -> str | None:
    """Get email password from AWS Secrets Manager."""
    if not BOTO3_AVAILABLE:
        logger.error("boto3 not available for AWS Secrets Manager access")
        return None

    try:
        client = boto3.client("secretsmanager", region_name="eu-west-2")
        response = client.get_secret_value(SecretId="the-alchemiser-secrets")
        secret_data = json.loads(response["SecretString"])

        # Look for email password in secrets (prioritize SMTP_PASSWORD)
        password = (
            secret_data.get("SMTP_PASSWORD")
            or secret_data.get("email_password")
            or secret_data.get("EMAIL_PASSWORD")
        )

        if not password:
            logger.warning("Email password not found in AWS Secrets Manager")
            return None

        logger.info("Successfully loaded email password from AWS Secrets Manager")
        return str(password)

    except ClientError as e:
        logger.error(f"Failed to retrieve email password from AWS: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving email password from AWS: {e}")
        return None


def _get_email_password_from_env() -> str | None:
    """Get email password from environment variables."""
    # First try the Pydantic config model (preferred method)
    try:
        config = load_settings()
        if config.email.password:
            logger.info("Successfully loaded email password from Pydantic config (EMAIL__PASSWORD)")
            return config.email.password
    except Exception as e:
        logger.debug(f"Could not load email password from Pydantic config: {e}")

    # Fallback to direct environment variable access for backward compatibility
    password = (
        os.getenv("EMAIL__PASSWORD")
        or os.getenv("EMAIL_PASSWORD")
        or os.getenv("EMAIL__SMTP_PASSWORD")
        or os.getenv("SMTP_PASSWORD")
    )

    if not password:
        logger.warning(
            "Email password not found in environment variables (tried EMAIL__PASSWORD, EMAIL_PASSWORD, EMAIL__SMTP_PASSWORD, SMTP_PASSWORD)"
        )
        return None

    logger.info("Successfully loaded email password from environment variables (fallback method)")
    return password
