#!/usr/bin/env python3
"""Business Unit: tooling | Status: current.

Robust extractor for multi-line JSON values in dotenv-style files.

Purpose:
- Safely read values like STRATEGY__DSL_FILES and STRATEGY__DSL_ALLOCATIONS
    even when they are formatted across multiple lines in .env files.
- Minify JSON to a single line for safe shell passing.

Usage:
    poetry run python scripts/extract_env_json.py --file .env --var STRATEGY__DSL_FILES

Outputs the value to stdout (single line). Exits with non-zero code if not found.

Constraints:
- No external dependencies beyond the standard library.
- Tolerates comments and whitespace before/after the JSON value.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


_VAR_RE_TEMPLATE = r"^%s\s*=\s*"


def _find_json_span(text: str, start_idx: int) -> tuple[int, int]:
    """Find the span of a JSON value starting at start_idx.

    Supports values that begin with "{" or "[" and may span multiple lines.
    Handles strings and escapes to avoid premature brace/bracket matching.
    Returns (value_start, value_end_exclusive).
    Raises ValueError if a well-formed span cannot be determined.
    """
    i = start_idx
    # Skip whitespace
    while i < len(text) and text[i].isspace():
        i += 1
    if i >= len(text) or text[i] not in "[{":
        # Not JSON container; take rest of line
        j = text.find("\n", i)
        return i, (len(text) if j == -1 else j)

    opening = text[i]
    closing = "]" if opening == "[" else "}"
    depth = 0
    in_string = False
    escape = False
    j = i

    while j < len(text):
        ch = text[j]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == opening:
                depth += 1
            elif ch == closing:
                depth -= 1
                if depth == 0:
                    # Include the closing bracket/brace
                    j += 1
                    # Trim trailing whitespace/comments on same line
                    return i, j
        j += 1
    raise ValueError("Unterminated JSON value; missing closing bracket/brace")


def extract_var_value(dotenv_text: str, var_name: str) -> str:
    """Extract a variable's value from dotenv text, normalizing JSON if present.

    If the value starts with "[" or "{", it will be parsed as JSON and
    re-dumped in a compact single-line form to avoid quoting issues.
    Otherwise the raw value (sans surrounding quotes) is returned.
    """
    pattern = re.compile(_VAR_RE_TEMPLATE % re.escape(var_name), re.MULTILINE)
    m = pattern.search(dotenv_text)
    if not m:
        raise KeyError(f"Variable {var_name} not found")

    value_start = m.end()
    span_start, span_end = _find_json_span(dotenv_text, value_start)
    raw_value = dotenv_text[span_start:span_end].strip()

    # If it looks like JSON, normalize to single-line minified form
    if raw_value and raw_value[0] in "[{":
        try:
            parsed = json.loads(raw_value)
            return json.dumps(parsed, separators=(",", ":"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON for {var_name}: {e}") from e

    # Otherwise, return raw single-line string (e.g., API keys)
    # Strip any surrounding quotes
    if (raw_value.startswith('"') and raw_value.endswith('"')) or (
        raw_value.startswith("'") and raw_value.endswith("'")
    ):
        raw_value = raw_value[1:-1]
    return raw_value


def main() -> int:
    """CLI entry point to extract a variable from a dotenv file.

    Returns process exit code (0 on success).
    """
    ap = argparse.ArgumentParser(
        description="Extract multi-line JSON env value from .env"
    )
    ap.add_argument("--file", required=True, help="Path to .env-like file")
    ap.add_argument("--var", required=True, help="Variable name to extract")
    args = ap.parse_args()

    try:
        text = Path(args.file).read_text(encoding="utf-8")
    except FileNotFoundError:
        print("", end="")
        return 2

    try:
        value = extract_var_value(text, args.var)
    except (KeyError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 3

    # Print the value only
    sys.stdout.write(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
