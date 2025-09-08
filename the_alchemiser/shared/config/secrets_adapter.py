#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Simple secrets helper for environment-aware credential loading.

This module provides a straightforward approach for loading secrets:
- Local development: Loads from environment variables (typically .env files)
- AWS Lambda: Loads from AWS Secrets Manager

Trading mode is determined by which credentials you choose to store where:
- Local .env: Put your paper trading keys
- AWS Secrets: Put your live trading keys
"""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)


def get_alpaca_keys() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca API keys from the appropriate source.
    
    Returns:
        Tuple of (api_key, secret_key, endpoint) or (None, None, None) if not found
    """
    # Simple: if in Lambda, use AWS; otherwise use .env
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        # In Lambda - get from AWS Secrets Manager
        return _get_alpaca_keys_from_aws()
    else:
        # Local dev - get from .env
        return _get_alpaca_keys_from_env()


def _get_alpaca_keys_from_env() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca keys from environment variables."""
    api_key = os.getenv("ALPACA_KEY")
    secret_key = os.getenv("ALPACA_SECRET")
    endpoint = os.getenv("ALPACA_ENDPOINT")
    
    if not api_key or not secret_key or not endpoint:
        logger.error("Missing Alpaca credentials in environment variables: ALPACA_KEY, ALPACA_SECRET, ALPACA_ENDPOINT")
        return None, None, None
    
    logger.info("Successfully loaded Alpaca credentials from environment variables")
    return api_key, secret_key, endpoint


def _get_alpaca_keys_from_aws() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca keys from AWS Secrets Manager."""
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError as e:
        logger.error("boto3 is required for AWS Secrets Manager")
        return None, None, None
    
    try:
        secret_name = "alchemiser/prod/alpaca"
        region_name = "eu-west-2"
        
        client = boto3.client("secretsmanager", region_name=region_name)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response["SecretString"]
        secret_dict = json.loads(secret_string)
        
        api_key = secret_dict.get("ALPACA_KEY")
        secret_key = secret_dict.get("ALPACA_SECRET")
        endpoint = secret_dict.get("ALPACA_ENDPOINT")
        
        if not api_key or not secret_key or not endpoint:
            logger.error(f"Missing Alpaca credentials in AWS secret {secret_name}")
            return None, None, None
        
        logger.info(f"Successfully loaded Alpaca credentials from AWS Secrets Manager")
        return api_key, secret_key, endpoint
        
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(f"AWS Secrets Manager error ({error_code}): {e}")
        return None, None, None
    except Exception as e:
        logger.error(f"Unexpected error retrieving AWS secret: {e}")
        return None, None, None


# Legacy compatibility functions (can be removed later if not needed)
def get_twelvedata_api_key() -> str | None:
    """Get TwelveData API key from environment variables."""
    api_key = os.getenv("TWELVEDATA_KEY")
    
    if not api_key:
        logger.warning("TwelveData API key not found in environment variables")
        return None
    
    logger.info("Successfully loaded TwelveData API key from environment")
    return api_key