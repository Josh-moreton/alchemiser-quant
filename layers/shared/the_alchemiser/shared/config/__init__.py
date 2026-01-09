"""Business Unit: shared | Status: current.

Configuration management for all modules.
"""

from .aws_config import DYNAMODB_RETRY_CONFIG, LAMBDA_INVOKE_CONFIG
from .config import Settings, load_settings
from .symbols_config import classify_symbol, get_etf_symbols, is_etf

# Backward compatibility alias
Config = Settings

__all__ = [
    "DYNAMODB_RETRY_CONFIG",
    "LAMBDA_INVOKE_CONFIG",
    "Config",
    "Settings",
    "classify_symbol",
    "get_etf_symbols",
    "is_etf",
    "load_settings",
]
