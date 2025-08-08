#!/usr/bin/env python3
"""
Comprehensive import fixer for the rearchitected codebase.
This script fixes all remaining import issues across the entire codebase.
"""

import re
from pathlib import Path


def fix_imports_in_file(file_path):
    """Fix imports in a single file."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Fix core.* imports to their new locations
        patterns = [
            # Core exceptions -> services.exceptions
            (r"from \.\.core\.exceptions import", "from the_alchemiser.services.exceptions import"),
            (
                r"from the_alchemiser\.core\.exceptions import",
                "from the_alchemiser.services.exceptions import",
            ),
            # Core logging -> infrastructure.logging
            (
                r"from \.\.core\.logging\.logging_utils import",
                "from the_alchemiser.infrastructure.logging.logging_utils import",
            ),
            (
                r"from the_alchemiser\.core\.logging\.logging_utils import",
                "from the_alchemiser.infrastructure.logging.logging_utils import",
            ),
            # Core registry -> domain.registry
            (r"from \.\.core\.registry import", "from the_alchemiser.domain.registry import"),
            (
                r"from the_alchemiser\.core\.registry import",
                "from the_alchemiser.domain.registry import",
            ),
            # Core types -> domain.types
            (r"from \.\.core\.types import", "from the_alchemiser.domain.types import"),
            (r"from the_alchemiser\.core\.types import", "from the_alchemiser.domain.types import"),
            # Core trading -> domain.strategies
            (
                r"from \.\.core\.trading\.strategy_manager import",
                "from the_alchemiser.domain.strategies.strategy_manager import",
            ),
            (
                r"from the_alchemiser\.core\.trading\.strategy_manager import",
                "from the_alchemiser.domain.strategies.strategy_manager import",
            ),
            # Core error_handler -> services.error_handler
            (
                r"from \.\.core\.error_handler import",
                "from the_alchemiser.services.error_handler import",
            ),
            (
                r"from the_alchemiser\.core\.error_handler import",
                "from the_alchemiser.services.error_handler import",
            ),
            # Utils logging -> infrastructure.logging
            (
                r"from \.\.utils\.logging\.logging_utils import",
                "from the_alchemiser.infrastructure.logging.logging_utils import",
            ),
            (
                r"from the_alchemiser\.utils\.logging\.logging_utils import",
                "from the_alchemiser.infrastructure.logging.logging_utils import",
            ),
            # Utils trading_math -> domain.math.trading_math
            (
                r"from \.\.utils\.trading_math import",
                "from the_alchemiser.domain.math.trading_math import",
            ),
            (
                r"from the_alchemiser\.utils\.trading_math import",
                "from the_alchemiser.domain.math.trading_math import",
            ),
            # Services UI -> interface.email or interface.cli
            (
                r"from the_alchemiser\.services\.ui import",
                "from the_alchemiser.interface.email.email_utils import",
            ),
            # Interface imports
            (
                r"from the_alchemiser\.interface\.cli_formatter import",
                "from the_alchemiser.interface.cli.cli_formatter import",
            ),
            (
                r"from the_alchemiser\.interface\.email_utils import",
                "from the_alchemiser.interface.email.email_utils import",
            ),
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        # Write back if changed
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Fix imports across the entire codebase."""
    project_root = Path(__file__).parent.parent
    files_fixed = 0

    # Process all Python files
    for py_file in project_root.rglob("*.py"):
        # Skip certain directories
        if any(skip in str(py_file) for skip in [".venv", "__pycache__", ".git", "build", "dist"]):
            continue

        if fix_imports_in_file(py_file):
            print(f"Fixed imports in {py_file}")
            files_fixed += 1

    print(f"\nFixed imports in {files_fixed} files")


if __name__ == "__main__":
    main()
