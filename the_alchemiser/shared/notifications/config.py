"""Business Unit: utilities; Status: current.

Email configuration management module.

This module handles loading email settings from environment variables and AWS Secrets Manager.
Replaces the `get_email_config` function from the original email_utils.py.
"""

from __future__ import annotations

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.config.secrets_adapter import get_email_password
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.notifications import EmailCredentials

logger = get_logger(__name__)


class EmailConfig:
    """Manages email configuration settings."""

    def __init__(self) -> None:
        """Prepare helpers for loading configuration from multiple sources."""
        self._config_cache: EmailCredentials | None = None

    def get_config(
        self,
    ) -> EmailCredentials | None:
        """Get email configuration from environment variables and secrets manager.

        Returns:
            EmailCredentials containing email configuration or None if configuration is invalid.

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
                logger.error("from_email not configured in environment variables")
                return None

            if not email_password:
                logger.warning("Email password not found - email notifications will be disabled")
                return None

            # Use from_email as to_email if to_email is not specified
            if not to_email:
                to_email = from_email

            logger.debug(
                f"Email config loaded: SMTP={smtp_server}:{smtp_port}, from={from_email}, to={to_email}"
            )

            self._config_cache = EmailCredentials(
                smtp_server=smtp_server,
                smtp_port=smtp_port,
                email_address=from_email,
                email_password=email_password,
                recipient_email=to_email,
            )
            return self._config_cache

        except Exception as e:
            logger.error(f"Error loading email configuration: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache = None

    def is_neutral_mode_enabled(self) -> bool:
        """Check if neutral mode is enabled for emails."""
        try:
            config = load_settings()
            return config.email.neutral_mode
        except Exception as e:
            logger.warning(f"Error checking neutral mode config: {e}")
            return False


# Global instance for backward compatibility
_email_config = EmailConfig()


def get_email_config() -> tuple[str, int, str, str, str] | None:
    """Get email configuration (backward compatibility function)."""
    config = _email_config.get_config()
    if config:
        return (
            config.smtp_server,
            config.smtp_port,
            config.email_address,
            config.email_password,
            config.recipient_email,
        )
    return None


def is_neutral_mode_enabled() -> bool:
    """Check if neutral mode is enabled for emails (standalone function)."""
    return _email_config.is_neutral_mode_enabled()
