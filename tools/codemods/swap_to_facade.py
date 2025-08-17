#!/usr/bin/env python3
"""Rewrite imports to use the data provider facade."""

from __future__ import annotations

import argparse
from pathlib import Path

TARGET = "the_alchemiser.infrastructure.data_providers.data_provider"
REPLACEMENT = "the_alchemiser.infrastructure.data_providers.unified_data_provider_facade"


def swap(root: Path, dry_run: bool = False) -> list[Path]:
    """Swap legacy provider imports for facade imports."""
    changed: list[Path] = []
    for path in root.rglob("*.py"):
        if "tests/contracts" in str(path) or path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text()
        if TARGET in text:
            changed.append(path)
            if not dry_run:
                path.write_text(text.replace(TARGET, REPLACEMENT))
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="show files but make no changes")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    files = swap(root, dry_run=args.dry_run)
    if files:
        print("Updated imports in:")
        for f in files:
            print(f.relative_to(root))
    else:
        print("No legacy imports found")


if __name__ == "__main__":
    main()
