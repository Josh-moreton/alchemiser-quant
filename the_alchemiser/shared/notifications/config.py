"""Business Unit: notifications; Status: current.

Email configuration management module.

This module handles loading email settings from environment variables and AWS Secrets Manager.
Replaces the `get_email_config` function from the original email_utils.py.
"""

from __future__ import annotations

import threading
import warnings

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.config.secrets_adapter import get_email_password
from the_alchemiser.shared.errors import ConfigurationError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.notifications import EmailCredentials

logger = get_logger(__name__)

# Module name constant for consistent logging
MODULE_NAME = "shared.notifications.config"


class EmailConfig:
    """Manages email configuration settings.

    This class provides cached configuration loading from environment variables
    and AWS Secrets Manager. Configuration is loaded once and cached for the
    lifetime of the instance unless explicitly cleared.

    Thread Safety:
        Instance methods are not thread-safe. Use the module-level functions
        which leverage a thread-safe singleton pattern.

    Attributes:
        _config_cache: Cached EmailCredentials instance (None until first load)
        _neutral_mode_cache: Cached neutral mode flag (None until first load)

    """

    def __init__(self) -> None:
        """Prepare helpers for loading configuration from multiple sources."""
        self._config_cache: EmailCredentials | None = None
        self._neutral_mode_cache: bool | None = None

    def get_config(self) -> EmailCredentials:
        """Get email configuration from environment variables and secrets manager.

        Configuration is loaded from:
        1. Environment variables (via Pydantic Settings)
        2. AWS Secrets Manager (for password, via secrets_adapter)

        Configuration is cached after first successful load. Call clear_cache()
        to force reload.

        Returns:
            EmailCredentials: Frozen DTO with SMTP configuration

        Raises:
            ConfigurationError: If required configuration is missing or invalid

        Examples:
            >>> config_loader = EmailConfig()
            >>> creds = config_loader.get_config()
            >>> print(f"SMTP: {creds.smtp_server}:{creds.smtp_port}")

        """
        if self._config_cache:
            return self._config_cache

        try:
            # Get configuration instance
            config = load_settings()

            # Extract values directly from Pydantic models
            smtp_server = config.email.smtp_server
            smtp_port = config.email.smtp_port
            from_email = config.email.from_email
            to_email = config.email.to_email

            # Get sensitive password from secrets adapter (environment-aware)
            email_password = get_email_password()

            # Validate required fields
            if not from_email:
                logger.error(
                    "from_email not configured in environment variables",
                    module=MODULE_NAME,
                )
                raise ConfigurationError(
                    "from_email is required but not configured in environment variables",
                    config_key="EMAIL__FROM_EMAIL",
                )

            if not email_password:
                logger.error(
                    "Email password not found - email notifications will be disabled",
                    module=MODULE_NAME,
                )
                raise ConfigurationError(
                    "Email password is required but not found in environment variables or secrets",
                    config_key="EMAIL__PASSWORD",
                )

            # Use from_email as to_email if to_email is not specified
            if not to_email:
                to_email = from_email

            # Cache neutral_mode alongside credentials
            self._neutral_mode_cache = config.email.neutral_mode

            logger.debug(
                "Email config loaded successfully",
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                has_credentials=bool(from_email and email_password),
                neutral_mode=self._neutral_mode_cache,
                module=MODULE_NAME,
            )

            self._config_cache = EmailCredentials(
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                email_address=from_email,
                email_password=email_password,
                recipient_email=to_email,
            )
            return self._config_cache

        except ConfigurationError:
            # Re-raise ConfigurationError as-is
            raise
        except Exception as e:
            logger.error(
                "Error loading email configuration",
                error=str(e),
                error_type=type(e).__name__,
                module=MODULE_NAME,
            )
            raise ConfigurationError(f"Failed to load email configuration: {e}") from e

    def clear_cache(self) -> None:
        """Clear the configuration cache.

        Forces reload on next get_config() call. Useful for:
        - Testing with different configuration values
        - Runtime configuration updates (rare)
        - Manual cache invalidation after config changes

        """
        self._config_cache = None
        self._neutral_mode_cache = None

    def is_neutral_mode_enabled(self) -> bool:
        """Check if neutral mode is enabled for emails.

        Returns cached value if available, otherwise loads from settings.
        Neutral mode is typically used to disable actual email sending in
        development/test environments.

        Returns:
            bool: True if neutral mode is enabled, False otherwise

        Raises:
            ConfigurationError: If configuration cannot be loaded

        """
        if self._neutral_mode_cache is not None:
            return self._neutral_mode_cache

        try:
            config = load_settings()
            self._neutral_mode_cache = config.email.neutral_mode
            return self._neutral_mode_cache
        except Exception as e:
            logger.error(
                "Error checking neutral mode config",
                error=str(e),
                error_type=type(e).__name__,
                module=MODULE_NAME,
            )
            raise ConfigurationError(f"Failed to check neutral mode configuration: {e}") from e


# Thread-safe singleton management
_email_config_lock = threading.Lock()
_email_config: EmailConfig | None = None


def _get_email_config_singleton() -> EmailConfig:
    """Get or create the global EmailConfig instance (thread-safe).

    Uses double-check locking pattern to ensure thread safety with
    minimal performance overhead.

    Returns:
        EmailConfig: Global singleton instance

    """
    global _email_config
    if _email_config is None:
        with _email_config_lock:
            if _email_config is None:
                _email_config = EmailConfig()
    return _email_config


def get_email_config() -> tuple[str, int, str, str, str] | None:
    """Get email configuration (backward compatibility function).

    .. deprecated:: 2.20.2
        Use EmailConfig().get_config() to get EmailCredentials DTO instead.
        This function returns a tuple for backward compatibility and will be
        removed in version 3.0.0.

    Returns:
        Tuple of (smtp_server, smtp_port, from_email, password, to_email) or None
        if configuration cannot be loaded.

    """
    warnings.warn(
        "get_email_config() is deprecated. Use EmailConfig().get_config() for DTO.",
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        config = _get_email_config_singleton().get_config()
        return (
            config.smtp_server,
            config.smtp_port,
            config.email_address,
            config.email_password,
            config.recipient_email,
        )
    except ConfigurationError:
        # Return None for backward compatibility with existing code
        # that checks for None return value
        logger.warning(
            "Email configuration unavailable",
            module=MODULE_NAME,
        )
        return None


def is_neutral_mode_enabled() -> bool:
    """Check if neutral mode is enabled for emails (standalone function).

    .. deprecated:: 2.20.2
        Use EmailConfig().is_neutral_mode_enabled() for better error handling.
        This function will be removed in version 3.0.0.

    Returns:
        bool: True if neutral mode is enabled, False on any error

    """
    warnings.warn(
        "is_neutral_mode_enabled() standalone function is deprecated. "
        "Use EmailConfig().is_neutral_mode_enabled() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        return _get_email_config_singleton().is_neutral_mode_enabled()
    except ConfigurationError:
        # Return False for backward compatibility
        logger.warning(
            "Neutral mode check failed, defaulting to False",
            module=MODULE_NAME,
        )
        return False
