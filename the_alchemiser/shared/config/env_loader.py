"""Business Unit: shared | Status: current.

Auto-load .env file into OS environment variables.

This module automatically loads the .env file when imported as a side-effect,
ensuring that environment variables are available via os.getenv() throughout
the application.

Side-effects:
    - Loads .env file from project root into os.environ on module import
    - Uses override=True: replaces existing environment variables with .env values
    - Falls back gracefully if python-dotenv is not installed
    - Logs loading activity for observability

Import pattern:
    from the_alchemiser.shared.config import env_loader  # noqa: F401

Error handling:
    - ImportError: If python-dotenv is not available, skips loading with warning
    - Missing .env: Logs info message, continues without error
    - Load errors: Catches and logs exceptions from load_dotenv

Security notes:
    - Loads all variables from .env file without validation
    - Secrets should be managed via secrets_adapter.py
    - Do not log environment variable values (could expose secrets)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logging import Logger

# Defer logger import to avoid circular dependency issues at module load time
# Will initialize logger only when needed
_logger: Logger | None = None


def _get_logger() -> Logger:
    """Lazy-load logger to avoid circular import issues."""
    global _logger
    if _logger is None:
        try:
            from the_alchemiser.shared.logging import get_logger

            _logger = get_logger(__name__)
        except ImportError:
            # Fallback to basic logging if shared.logging not available yet
            import logging

            _logger = logging.getLogger(__name__)
    return _logger


# Guard to prevent double-loading on module reload
_ENV_LOADED = False

try:
    from dotenv import load_dotenv

    if not _ENV_LOADED:
        # Find the .env file in the project root
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent  # Go up to the project root
        env_file = project_root / ".env"

        if env_file.exists():
            try:
                # Load the .env file into OS environment
                # override=True: .env values take precedence over existing env vars
                result = load_dotenv(env_file, override=True)

                logger = _get_logger()
                if result:
                    logger.info(
                        "Environment variables loaded from .env file",
                        extra={
                            "env_file": str(env_file),
                            "module": __name__,
                        },
                    )
                else:
                    logger.warning(
                        "Failed to load .env file (dotenv returned False)",
                        extra={
                            "env_file": str(env_file),
                            "module": __name__,
                        },
                    )

            except Exception as e:
                logger = _get_logger()
                logger.error(
                    "Error loading .env file",
                    extra={
                        "env_file": str(env_file),
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "module": __name__,
                    },
                )
                # Don't raise - allow application to continue with existing env vars
        else:
            # .env file not found - this is expected in CI/production environments
            logger = _get_logger()
            logger.info(
                ".env file not found, skipping environment variable loading",
                extra={
                    "expected_path": str(env_file),
                    "module": __name__,
                },
            )

        _ENV_LOADED = True

except ImportError:
    # python-dotenv not available - this should not happen in production
    # but handle gracefully for edge cases
    if not _ENV_LOADED:
        # Try to log warning if possible, otherwise write to stderr
        try:
            logger = _get_logger()
            logger.warning(
                "python-dotenv not available, skipping .env file loading",
                extra={
                    "module": __name__,
                    "python_path": sys.executable,
                },
            )
        except Exception:
            # Last resort: print to stderr if logging fails
            print(
                f"WARNING: {__name__}: python-dotenv not available, skipping .env file loading",
                file=sys.stderr,
            )

        _ENV_LOADED = True
