"""Business Unit: shared | Status: current.

Configuration management for all modules.
"""

from .config import Settings, load_settings
from .symbols_config import classify_symbol, get_etf_symbols, is_etf

# Backward compatibility alias
Config = Settings

__all__ = [
    "Config",
    "Settings",
    "classify_symbol",
    "get_etf_symbols",
    "is_etf",
    "load_settings",
]
