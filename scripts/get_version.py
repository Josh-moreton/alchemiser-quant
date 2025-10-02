#!/usr/bin/env python3
"""Extract version from pyproject.toml for build-time injection.

This script reads the version from pyproject.toml and outputs it to stdout.
It's used during the SAM build process to inject version metadata into the Lambda function.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path


def get_version() -> str:
    """Read version from pyproject.toml.

    Returns:
        Version string from pyproject.toml

    Raises:
        FileNotFoundError: If pyproject.toml is not found
        KeyError: If version field is missing
        Exception: For other parsing errors

    """
    # Find pyproject.toml in project root (one level up from scripts/)
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    try:
        version = data["tool"]["poetry"]["version"]
        return version
    except KeyError as e:
        raise KeyError(f"Version not found in pyproject.toml: {e}") from e


if __name__ == "__main__":
    try:
        version = get_version()
        print(version)
    except Exception as e:
        print(f"Error reading version: {e}", file=sys.stderr)
        sys.exit(1)
