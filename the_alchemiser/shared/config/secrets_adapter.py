#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Simple environment variable-based secrets helper.

This module provides the simplest possible approach for loading secrets:
- All environments (local dev, Lambda, GitHub Actions) provide credentials via environment variables
- Local development: .env file populates environment variables
- AWS Lambda: Environment variables pre-populated from AWS Secrets Manager at deploy time
- GitHub Actions: Repository secrets injected as environment variables

The application code only ever reads environment variables - no conditional logic.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def get_alpaca_keys() -> tuple[str, str, str] | tuple[None, None, None]:
    """Get Alpaca API keys from environment variables.
    
    Returns:
        Tuple of (api_key, secret_key, endpoint) or (None, None, None) if not found
    """
    api_key = os.getenv("ALPACA_KEY")
    secret_key = os.getenv("ALPACA_SECRET")
    endpoint = os.getenv("ALPACA_ENDPOINT")
    
    if not api_key or not secret_key or not endpoint:
        logger.error("Missing Alpaca credentials in environment variables: ALPACA_KEY, ALPACA_SECRET, ALPACA_ENDPOINT")
        return None, None, None
    
    logger.info("Successfully loaded Alpaca credentials from environment variables")
    return api_key, secret_key, endpoint


def get_twelvedata_api_key() -> str | None:
    """Get TwelveData API key from environment variables."""
    api_key = os.getenv("TWELVEDATA_KEY")
    
    if not api_key:
        logger.warning("TwelveData API key not found in environment variables")
        return None
    
    logger.info("Successfully loaded TwelveData API key from environment")
    return api_key