"""Business Unit: shared | Status: current.

Credential/environment loading and feed selection logic for pricing service.
"""

from __future__ import annotations

import logging
import os
from typing import NamedTuple

logger = logging.getLogger(__name__)


class PricingServiceConfig(NamedTuple):
    """Configuration for pricing service initialization."""
    
    api_key: str
    secret_key: str
    paper_trading: bool
    max_symbols: int
    feed: str


def load_pricing_config(
    api_key: str | None = None,
    secret_key: str | None = None,
    *,
    paper_trading: bool = True,
    max_symbols: int = 30,
) -> PricingServiceConfig:
    """Load and validate pricing service configuration.
    
    Args:
        api_key: Alpaca API key (reads from env if not provided)
        secret_key: Alpaca secret key (reads from env if not provided)
        paper_trading: Whether to use paper trading endpoints
        max_symbols: Maximum number of symbols to subscribe to concurrently
        
    Returns:
        PricingServiceConfig with validated configuration
        
    Raises:
        ValueError: If credentials are not provided or found in environment

    """
    # Load credentials from environment if not provided
    resolved_api_key, resolved_secret_key = _load_credentials(api_key, secret_key)
    
    # Resolve data feed
    feed = _resolve_data_feed()
    
    return PricingServiceConfig(
        api_key=resolved_api_key,
        secret_key=resolved_secret_key,
        paper_trading=paper_trading,
        max_symbols=max_symbols,
        feed=feed,
    )


def _load_credentials(api_key: str | None, secret_key: str | None) -> tuple[str, str]:
    """Load and validate Alpaca credentials.
    
    Args:
        api_key: API key or None to load from environment
        secret_key: Secret key or None to load from environment
        
    Returns:
        Tuple of (api_key, secret_key)
        
    Raises:
        ValueError: If credentials are not provided or found in environment

    """
    if not api_key or not secret_key:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            logger.debug("python-dotenv not available, skipping .env file loading")
            
        api_key = api_key or os.getenv("ALPACA_KEY")
        secret_key = secret_key or os.getenv("ALPACA_SECRET")

    if not api_key or not secret_key:
        logger.error("❌ Alpaca credentials not provided or found in environment")
        raise ValueError(
            "Alpaca API credentials required. Set ALPACA_KEY and ALPACA_SECRET "
            "environment variables or pass them as parameters."
        )
    
    logger.info("✅ Alpaca credentials loaded successfully")
    return api_key, secret_key


def _resolve_data_feed() -> str:
    """Resolve the Alpaca data feed to use.
    
    Allows overriding via env vars `ALPACA_FEED` or `ALPACA_DATA_FEED`.
    Defaults to "iex". Use "sip" if you have the required subscription.
    
    Returns:
        Data feed name ("iex" or "sip")

    """
    feed = (os.getenv("ALPACA_FEED") or os.getenv("ALPACA_DATA_FEED") or "iex").lower()
    
    if feed not in {"iex", "sip"}:
        logger.warning(f"Unknown ALPACA_FEED '{feed}', defaulting to 'iex'")
        return "iex"
    
    logger.info(f"📡 Using Alpaca data feed: {feed}")
    return feed


def validate_config(config: PricingServiceConfig) -> None:
    """Validate pricing service configuration.
    
    Args:
        config: Configuration to validate
        
    Raises:
        ValueError: If configuration is invalid

    """
    if not config.api_key or not config.secret_key:
        raise ValueError("API key and secret key are required")
        
    if config.max_symbols < 1:
        raise ValueError("max_symbols must be at least 1")
        
    if config.feed not in {"iex", "sip"}:
        raise ValueError(f"Invalid feed '{config.feed}', must be 'iex' or 'sip'")
        
    logger.debug(f"✅ Configuration validated: {config.max_symbols} max symbols, {config.feed} feed, {'paper' if config.paper_trading else 'live'} trading")