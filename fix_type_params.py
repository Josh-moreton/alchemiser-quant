#!/usr/bin/env python3
"""Quick script to fix common type parameter issues."""

import re
import subprocess


def fix_file_type_params(filepath):
    """Fix common type parameter patterns in a file."""
    try:
        with open(filepath) as f:
            content = f.read()

        original_content = content

        # Add typing import if needed and Any is used
        if "dict[str, Any]" in content or "list[Any]" in content:
            if "from typing import" not in content and "import typing" not in content:
                # Find the first import and add after it
                import_match = re.search(r"^(import .+)$", content, re.MULTILINE)
                if import_match:
                    content = content.replace(
                        import_match.group(1), import_match.group(1) + "\nfrom typing import Any"
                    )

        # Common type parameter fixes
        patterns = [
            # Function parameters and return types
            (r"-> dict\):", r"-> dict[str, Any]):"),
            (r"-> list\):", r"-> list[Any]):"),
            (r"-> tuple\):", r"-> tuple[Any, ...]):"),
            (r": dict\)", r": dict[str, Any])"),
            (r": list\)", r": list[Any])"),
            (r": tuple\)", r": tuple[Any, ...])"),
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        # Only write if changed
        if content != original_content:
            with open(filepath, "w") as f:
                f.write(content)
            return True
        return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """Find Python files with type-arg errors and fix them."""
    # Get files with type-arg errors
    result = subprocess.run(
        [
            "python",
            "-m",
            "mypy",
            "the_alchemiser",
            "--show-error-codes",
            "--pretty",
            "--ignore-missing-imports",
        ],
        capture_output=True,
        text=True,
        cwd="/Users/joshua.moreton/Documents/GitHub/the-alchemiser",
    )

    # Extract unique file paths with type-arg errors
    type_arg_files = set()
    for line in result.stdout.split("\n"):
        if "[type-arg]" in line and ".py:" in line:
            file_match = re.search(r"(the_alchemiser/[^:]+\.py)", line)
            if file_match:
                type_arg_files.add(file_match.group(1))

    print(f"Found {len(type_arg_files)} files with type-arg errors")

    # Process each file
    fixed_count = 0
    for relative_path in sorted(type_arg_files):
        full_path = f"/Users/joshua.moreton/Documents/GitHub/the-alchemiser/{relative_path}"
        if fix_file_type_params(full_path):
            fixed_count += 1
            print(f"Fixed: {relative_path}")

    print(f"Fixed {fixed_count} files")


if __name__ == "__main__":
    main()
