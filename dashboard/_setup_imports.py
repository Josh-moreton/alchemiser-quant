"""Import path setup for dashboard application.

This module configures Python's import path to work with the Lambda layers architecture.

Architecture Overview:
======================
Production (AWS Lambda):
  - Shared layer: /opt/python/the_alchemiser/shared/
  - Function code: /var/task/

Local Development (Dashboard):
  - Shared layer: shared_layer/python/the_alchemiser/shared/
  - Function code: functions/*/the_alchemiser/*/

This module adds the layers to sys.path so the dashboard can import:
  - from the_alchemiser.shared.* (always available)
  - from the_alchemiser.shared.data_v2.* (in shared layer)

Usage:
    # At the top of your module (after stdlib imports, before local imports):
    import _setup_imports  # noqa: F401 (imported for side effects)

    # Now you can import shared modules:
    from the_alchemiser.shared.logging import get_logger
    from the_alchemiser.shared.config import load_settings
"""

from __future__ import annotations

import sys
from pathlib import Path

# Get project root (parent of dashboard/)
PROJECT_ROOT = Path(__file__).parent.parent

# Add shared layer to path (contains the_alchemiser.shared.*)
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
