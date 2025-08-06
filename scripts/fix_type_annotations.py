#!/usr/bin/env python3
"""
Phase 16c: Batch Type Annotation Fixes

This script automatically fixes common missing type annotations to enable
disallow_untyped_defs in mypy configuration.
"""

import re
from pathlib import Path

# Common type annotation patterns
TYPE_FIXES = [
    # Constructor patterns
    (r"def __init__\(self\):", "def __init__(self) -> None:"),
    (r"def __init__\(self, ([^)]+)\):", r"def __init__(self, \1) -> None:"),
    # Common main function patterns
    (r"def main\(\):", "def main() -> None:"),
    # Simple void functions
    (r"def load_config\(self\):", "def load_config(self) -> None:"),
    (r"def clear_cache\(self\):", "def clear_cache(self) -> None:"),
    (r"def reload_execution_config\(\):", "def reload_execution_config() -> None:"),
    (r"def run_once\(self\):", "def run_once(self) -> None:"),
    (
        r"def update_performance\(self, return_value: float\):",
        "def update_performance(self, return_value: float) -> None:",
    ),
    (
        r"def log_decision\(self, symbol_or_allocation: str \| dict\[str, float\]\):",
        "def log_decision(self, symbol_or_allocation: str | dict[str, float]) -> None:",
    ),
    # Return type functions
    (r"def get_market_data\(self\):", "def get_market_data(self) -> dict[str, Any]:"),
    (r"def get_account_info\(self\):", "def get_account_info(self) -> dict[str, Any]:"),
    (r"def get_positions\(self\):", "def get_positions(self) -> list[dict[str, Any]]:"),
    (r"def get_open_positions\(self\):", "def get_open_positions(self) -> list[dict[str, Any]]:"),
    (r"def get_cache_stats\(self\):", "def get_cache_stats(self) -> dict[str, Any]:"),
    (
        r"def get_current_portfolio_allocation\(self\):",
        "def get_current_portfolio_allocation(self) -> dict[str, float]:",
    ),
    (r"def get_websocket_stream\(self\):", "def get_websocket_stream(self) -> Any:"),
    (r"def get_websocket_thread\(self\):", "def get_websocket_thread(self) -> Any:"),
    (r"def to_dict\(self\):", "def to_dict(self) -> dict[str, Any]:"),
    (r"def _get_config\(self\):", "def _get_config(self) -> Any:"),
    (r"def load_alert_config\(\):", "def load_alert_config() -> dict[str, Any]:"),
    # Specific function patterns with parameters
    (r"def settings_customise_sources\(\s*cls,", "def settings_customise_sources(cls,"),
    (r"def from_settings\(cls\):", "def from_settings(cls) -> 'ExecutionConfig':"),
]

# Files that need Any import
FILES_NEED_ANY = [
    "the_alchemiser/utils/price_utils.py",
    "the_alchemiser/core/config.py",
    "the_alchemiser/lambda_handler.py",
    "the_alchemiser/main.py",
]


def add_typing_imports(file_path: Path) -> bool:
    """Add necessary typing imports to a file."""
    content = file_path.read_text()
    lines = content.split("\n")

    # Check if Any is already imported
    has_any_import = any("from typing import" in line and "Any" in line for line in lines)
    has_typing_import = any(line.startswith("from typing import") for line in lines)

    if has_any_import:
        return False

    # Find where to insert the import
    insert_index = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_index = i
            break

    # Add the import
    if has_typing_import:
        # Find existing typing import and add Any
        for i, line in enumerate(lines):
            if line.startswith("from typing import"):
                if "Any" not in line:
                    lines[i] = line.rstrip() + ", Any"
                break
    else:
        # Add new typing import
        lines.insert(insert_index, "from typing import Any")
        lines.insert(insert_index + 1, "")

    # Write back
    file_path.write_text("\n".join(lines))
    return True


def fix_type_annotations_in_file(file_path: Path) -> int:
    """Fix type annotations in a single file."""
    content = file_path.read_text()
    fixes_applied = 0

    for pattern, replacement in TYPE_FIXES:
        new_content, count = re.subn(pattern, replacement, content)
        if count > 0:
            content = new_content
            fixes_applied += count
            print(f"  Fixed {count} occurrences of: {pattern}")

    if fixes_applied > 0:
        file_path.write_text(content)

    return fixes_applied


def main() -> None:
    """Apply batch type annotation fixes."""
    print("🔧 Phase 16c: Applying Batch Type Annotation Fixes")
    print("=" * 60)

    # Find all Python files in the main package
    project_root = Path(__file__).parent.parent
    alchemiser_path = project_root / "the_alchemiser"

    python_files = list(alchemiser_path.rglob("*.py"))
    total_fixes = 0

    # Add typing imports where needed
    print("\n📦 Adding typing imports...")
    for file_path in python_files:
        relative_path = file_path.relative_to(project_root)
        if str(relative_path) in FILES_NEED_ANY or "the_alchemiser/" in str(relative_path):
            if add_typing_imports(file_path):
                print(f"  ✅ Added typing imports to: {relative_path}")

    print(f"\n🔨 Fixing type annotations in {len(python_files)} files...")

    for file_path in python_files:
        relative_path = file_path.relative_to(project_root)
        print(f"\n📁 Processing: {relative_path}")

        try:
            fixes = fix_type_annotations_in_file(file_path)
            if fixes > 0:
                total_fixes += fixes
                print(f"  ✅ Applied {fixes} type annotation fixes")
            else:
                print("  ✓ No fixes needed")

        except Exception as e:
            print(f"  ❌ Error processing {relative_path}: {e}")

    print("\n🎯 Batch Type Annotation Fixes Complete!")
    print(f"   Total fixes applied: {total_fixes}")
    print(f"   Files processed: {len(python_files)}")
    print("\n📝 Next steps:")
    print("   1. Run: python -m mypy the_alchemiser/ --no-error-summary")
    print("   2. Review any remaining type annotation errors")
    print("   3. Proceed to Phase 16c Step 2: Enable disallow_untyped_calls")


if __name__ == "__main__":
    main()
