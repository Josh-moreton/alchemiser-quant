"""Business Unit: scripts | Status: current.

Import path setup for scripts that need access to the shared Lambda layer.

This module configures Python's import path to work with the Lambda layers
architecture so that scripts can import from ``the_alchemiser.shared.*``.

Architecture Overview:
======================
Production (AWS Lambda):
  - Shared layer: /opt/python/the_alchemiser/shared/
  - Function code: /var/task/

Local Development (Scripts):
  - Shared layer: shared_layer/python/the_alchemiser/shared/
  - Function code: functions/*/

Usage:
    # At the top of your script (after stdlib imports, before local imports):
    import _setup_imports  # noqa: F401 (imported for side effects)

    # Now you can import shared modules:
    from the_alchemiser.shared.logging import get_logger
    from the_alchemiser.shared.config import load_settings
"""

from __future__ import annotations

import sys
from pathlib import Path

# Get project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).parent.parent

# Add shared layer to path (contains the_alchemiser.shared.*)
# Note: the Lambda layer convention places Python packages under python/
SHARED_LAYER_PATH = PROJECT_ROOT / "shared_layer" / "python"

if SHARED_LAYER_PATH.exists():
    sys.path.insert(0, str(SHARED_LAYER_PATH))
else:
    msg = (
        f"ERROR: Shared layer not found at {SHARED_LAYER_PATH}\n"
        "This module requires the Lambda layers architecture.\n"
        "See CLAUDE.md for project structure."
    )
    raise RuntimeError(msg)

# Export for modules that need to reference project structure
__all__ = ["PROJECT_ROOT", "SHARED_LAYER_PATH"]
