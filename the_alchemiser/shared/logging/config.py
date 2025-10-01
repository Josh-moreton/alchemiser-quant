"""Business Unit: shared | Status: current.

Configuration management for logging system.

This module provides application-level logging configuration functions for different
environments including production, test, and development configurations.
"""

from __future__ import annotations

import logging
import os

from .core import get_logger, setup_logging
from .utils import _is_lambda_production_environment, _parse_log_level, _should_suppress_s3_logging


def configure_test_logging(log_level: int = logging.WARNING) -> None:
    """Configure logging specifically for test environments."""
    setup_logging(
        log_level=log_level,
        console_level=log_level,
        suppress_third_party=True,
        structured_format=False,  # Use human-readable format for tests
    )


def configure_production_logging(
    log_level: int = logging.INFO,
    log_file: str | None = None,
    *,
    console_level: int | None = None,
) -> None:
    """Configure logging for production environment with structured format.

    In Lambda environments, defaults to CloudWatch-only logging unless S3 is explicitly enabled.

    Args:
        log_level: Base log level for handlers.
        log_file: Optional path/URI for file logging.
        console_level: Override for console handler level. When None, defaults to `log_level`.

    """
    # Production hygiene: Only allow S3 logging if explicitly enabled
    if _should_suppress_s3_logging(log_file):
        logger = get_logger(__name__)
        logger.info("Lambda production mode: defaulting to CloudWatch-only logging")
        log_file = None

    setup_logging(
        log_level=log_level,
        log_file=log_file,
        console_level=console_level if console_level is not None else log_level,
        suppress_third_party=True,
        structured_format=True,  # Use JSON format for production
        enable_file_rotation=True,
        respect_existing_handlers=False,  # Production always controls logging
    )


def resolve_log_level(*, is_production: bool) -> int:
    """Resolve the desired log level from environment or settings.

    Args:
        is_production: Whether running in production environment

    Returns:
        Log level as integer

    """
    # Environment override first
    env_level = _parse_log_level(os.getenv("LOGGING__LEVEL"))
    if env_level is not None:
        return env_level

    # Then settings
    try:
        from the_alchemiser.shared.config.config import load_settings

        settings = load_settings()
        configured = _parse_log_level(getattr(settings.logging, "level", None))
        if configured is not None:
            return configured
    except (AttributeError, TypeError, ImportError):
        # Settings loading failed or invalid log level, fall back to default
        pass

    # Fallback
    return logging.INFO if is_production else logging.WARNING


def _load_application_settings() -> object | None:
    """Load application settings with error handling."""
    try:
        from the_alchemiser.shared.config.config import load_settings

        return load_settings()
    except (AttributeError, ImportError, TypeError):
        return None


def _determine_production_log_file(settings: object | None) -> str | None:
    """Determine log file for production environment."""
    if not settings:
        return None
    if (
        hasattr(settings, "logging")
        and getattr(settings.logging, "enable_s3_logging", False)
        and getattr(settings.logging, "s3_log_uri", None)
    ):
        return str(getattr(settings.logging, "s3_log_uri", None))
    return None


def _determine_production_console_level(settings: object | None) -> int | None:
    """Determine console level for production environment."""
    console_level = _parse_log_level(os.getenv("LOGGING__CONSOLE_LEVEL"))
    if console_level is not None:
        return console_level

    if not settings or not hasattr(settings, "logging"):
        return None

    settings_console_value = getattr(settings.logging, "console_level", None)
    if settings_console_value is not None:
        return _parse_log_level(str(settings_console_value))

    return None


def _configure_production_logging(resolved_level: int, settings: object | None) -> None:
    """Configure logging for production environment."""
    log_file = _determine_production_log_file(settings)
    console_level = _determine_production_console_level(settings)

    configure_production_logging(
        log_level=resolved_level,
        log_file=log_file,
        console_level=console_level,
    )


def _determine_development_console_level(default_level: int, settings: object | None) -> int:
    """Determine console level for development environment."""
    env_console = _parse_log_level(os.getenv("LOGGING__CONSOLE_LEVEL"))
    if env_console is not None:
        return env_console

    if settings and hasattr(settings, "logging"):
        configured_console = _parse_log_level(str(settings.logging.console_level))
        if configured_console is not None:
            return configured_console

    return default_level


def _determine_development_log_file(settings: object | None) -> str | None:
    """Determine log file for development environment."""
    env_path = os.getenv("LOGGING__LOCAL_LOG_FILE")
    if env_path and env_path.strip():
        return env_path

    if settings and hasattr(settings, "logging"):
        local_log_file = getattr(settings.logging, "local_log_file", None)
        if local_log_file:
            path = str(local_log_file).strip()
            return path or None

    return None


def _configure_development_logging(resolved_level: int, settings: object | None) -> None:
    """Configure logging for development environment."""
    setup_logging(
        log_level=resolved_level,
        log_file=_determine_development_log_file(settings),
        console_level=_determine_development_console_level(resolved_level, settings),
        suppress_third_party=True,
        structured_format=False,
        respect_existing_handlers=True,
    )


def _should_skip_logging_setup(root_logger: logging.Logger, *, is_production: bool) -> bool:
    """Determine if logging setup should be skipped."""
    return root_logger.hasHandlers() and not is_production


def configure_application_logging() -> None:
    """Configure application logging with reduced complexity."""
    is_production = _is_lambda_production_environment()
    root_logger = logging.getLogger()

    if _should_skip_logging_setup(root_logger, is_production=is_production):
        return

    resolved_level = resolve_log_level(is_production=is_production)
    settings = _load_application_settings()

    if is_production:
        _configure_production_logging(resolved_level, settings)
    else:
        _configure_development_logging(resolved_level, settings)
