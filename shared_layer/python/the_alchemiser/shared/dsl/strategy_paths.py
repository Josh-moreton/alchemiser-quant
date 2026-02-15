"""Business Unit: shared | Status: current.

Strategy file path resolution utilities.

Resolves the location of strategy .clj files across Lambda runtime
(shared layer at /opt/python/) and local development environments.
"""

from __future__ import annotations

import os
from pathlib import Path

# Resolved once: the repo root relative to this shared-layer file.
_SHARED_LAYER_STRATEGIES = (
    Path(__file__).resolve().parent.parent / "strategies"
)


def get_strategies_dir() -> Path:
    """Resolve the directory containing strategy .clj files.

    Resolution order:
    1. Lambda runtime path: ``/opt/python/the_alchemiser/shared/strategies/``
    2. Shared-layer relative path (works from any caller).
    3. ``STRATEGIES_DIR`` environment variable.

    Returns:
        Path to the strategies directory.

    Raises:
        ValueError: If no strategies directory can be found.

    """
    # Lambda runtime path (shared layer mounted at /opt/python)
    lambda_path = Path("/opt/python/the_alchemiser/shared/strategies")
    if lambda_path.exists():
        return lambda_path

    # Shared-layer relative path (works for both function code and scripts)
    if _SHARED_LAYER_STRATEGIES.exists():
        return _SHARED_LAYER_STRATEGIES

    # Explicit override via environment variable
    env_dir = os.environ.get("STRATEGIES_DIR", "")
    if env_dir:
        env_path = Path(env_dir)
        if env_path.exists():
            return env_path

    raise ValueError(
        "Cannot locate strategies directory. Set STRATEGIES_DIR environment variable."
    )
