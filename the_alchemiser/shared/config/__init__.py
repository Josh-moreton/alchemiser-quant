"""Business Unit: shared | Status: current.

Configuration management for all modules.
"""

from .config import Settings, load_settings

# Backward compatibility alias
Config = Settings

__all__ = ["Config", "Settings", "load_settings"]
