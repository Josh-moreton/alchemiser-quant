"""Email configuration management module.

This module handles loading email settings from environment variables and AWS Secrets Manager.
Replaces the `get_email_config` function from the original email_utils.py.
"""

import logging

from the_alchemiser.infrastructure.config import load_settings
from the_alchemiser.infrastructure.secrets.secrets_manager import SecretsManager
from the_alchemiser.interfaces.schemas.reporting import EmailCredentials


class EmailConfig:
    """Manages email configuration settings."""

    def __init__(self) -> None:
        """Prepare helpers for loading configuration from multiple sources."""

        self.secrets_manager = SecretsManager()
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

            # Get secrets manager config
            secret_name = config.secrets_manager.secret_name

            # Get sensitive password from AWS Secrets Manager
            email_password = self._get_email_password(secret_name)

            # Validate required fields
            if not from_email:
                logging.error("from_email not configured in environment variables")
                return None

            if not email_password:
                logging.error("email_password not found in AWS Secrets Manager")
                return None

            # Use from_email as to_email if to_email is not specified
            if not to_email:
                to_email = from_email

            logging.info(
                f"Email config loaded: SMTP={smtp_server}:{smtp_port}, from={from_email}, to={to_email}"
            )

            self._config_cache = {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "email_address": from_email,
                "email_password": email_password,
                "recipient_email": to_email,
            }
            return self._config_cache

        except Exception as e:
            logging.error(f"Error loading email configuration: {e}")
            return None

    def _get_email_password(self, secret_name: str) -> str | None:
        """Get email password from AWS Secrets Manager."""
        try:
            secrets = self.secrets_manager.get_secret(secret_name)
            if secrets:
                # Look for email password in secrets (prioritize SMTP_PASSWORD)
                return (
                    secrets.get("SMTP_PASSWORD")
                    or secrets.get("email_password")
                    or secrets.get("EMAIL_PASSWORD")
                )
        except Exception as e:
            logging.warning(f"Could not get email password from secrets manager: {e}")
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
            logging.warning(f"Error checking neutral mode config: {e}")
            return False


# Global instance for backward compatibility
_email_config = EmailConfig()


def get_email_config() -> tuple[str, int, str, str, str] | None:
    """Get email configuration (backward compatibility function)."""
    config = _email_config.get_config()
    if config:
        return (
            config["smtp_server"],
            config["smtp_port"],
            config["email_address"],
            config["email_password"],
            config["recipient_email"],
        )
    return None


def is_neutral_mode_enabled() -> bool:
    """Check if neutral mode is enabled for emails (standalone function)."""
    return _email_config.is_neutral_mode_enabled()
