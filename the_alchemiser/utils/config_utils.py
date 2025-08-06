"""
Configuration Utilities

This module provides helper functions for configuration loading operations.
"""

import json
import logging
import os
from typing import Any


def load_alert_config() -> dict[str, Any]:
    """
    Load alert configuration from S3 or local file with fallback to default values.

    This function attempts to load alert configuration in the following order:
    1. From S3 bucket (if configured and available)
    2. From local 'alert_config.json' file
    3. Default configuration from global config

    Returns:
        dict: The loaded configuration dictionary with alert settings.
    """
    try:
        # Try to load from S3 first, then local
        from the_alchemiser.core.utils.s3_utils import get_s3_handler

        s3_handler = get_s3_handler()

        # Check if file exists in S3 bucket
        from the_alchemiser.core.config import load_settings

        global_config = load_settings()
        s3_uri = global_config.alerts.alert_config_s3 or "s3://the-alchemiser-s3/alert_config.json"
        if s3_handler.file_exists(s3_uri):
            content = s3_handler.read_text(s3_uri)
            if content:
                return json.loads(content)

        # Fallback to local file
        if os.path.exists("alert_config.json"):
            with open("alert_config.json") as f:
                return json.load(f)

    except (ImportError, FileNotFoundError, OSError, ValueError, KeyError, AttributeError) as e:
        logging.warning(f"Could not load alert config: {e}")

    # Default config if nothing found - use global config values
    from the_alchemiser.core.config import load_settings

    global_config = load_settings()
    return {"alerts": {"cooldown_minutes": global_config.alerts.cooldown_minutes}}
