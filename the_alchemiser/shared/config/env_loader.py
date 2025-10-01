"""Business Unit: shared | Status: current.

Auto-load .env file into OS environment variables.

This module automatically loads the nearest `.env` file when imported so
environment variables are available via ``os.getenv()``. It prefers a
repository-root `.env` discovered via python-dotenv's `find_dotenv`, with a
fallback walk-up from this file's location. Values from `.env` will override
any existing OS environment values for the current process (override=True).
"""

import os
from pathlib import Path

try:
    from dotenv import find_dotenv, load_dotenv

    # 1) Prefer a .env discovered from the current working directory upwards
    dotenv_path = find_dotenv(usecwd=True)

    # 2) Fallback: walk up from this file's directory to locate a .env
    if not dotenv_path:
        module_path = Path(__file__).resolve()
        for ancestor in [module_path, *list(module_path.parents)]:
            candidate = (ancestor.parent if ancestor.is_file() else ancestor) / ".env"
            if candidate.exists():
                dotenv_path = str(candidate)
                break

    # Load if found
    if dotenv_path:
        load_dotenv(dotenv_path, override=True)
        # Expose the resolved dotenv path for diagnostics (no secrets)
        os.environ["ALCHEMISER_LOADED_ENV"] = str(dotenv_path)

except ImportError:
    # python-dotenv not available, skip silently
    pass
