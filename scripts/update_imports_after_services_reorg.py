"""
Update imports across the repository after reorganizing the services package.

Run in dry-run mode first (default), then with --apply to make changes.

Usage:
  poetry run python scripts/update_imports_after_services_reorg.py           # dry run
  poetry run python scripts/update_imports_after_services_reorg.py --apply  # write changes
  poetry run python scripts/update_imports_after_services_reorg.py --verbose

The script updates both `from ... import ...` and `import ...` statements.
It is conservative and uses regex boundaries to avoid accidental changes.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT

# Mapping of fully-qualified module paths (prefix only) to their new locations
MODULE_MAP: dict[str, str] = {
    # Enhanced -> new structured
    "the_alchemiser.services.enhanced.account_service": "the_alchemiser.services.account.account_service",
    "the_alchemiser.services.enhanced.market_data_service": "the_alchemiser.services.market_data.market_data_service",
    "the_alchemiser.services.enhanced.order_service": "the_alchemiser.services.trading.order_service",
    "the_alchemiser.services.enhanced.position_service": "the_alchemiser.services.trading.position_service",
    "the_alchemiser.services.enhanced.trading_service_manager": "the_alchemiser.services.trading.trading_service_manager",
    # Root -> structured
    "the_alchemiser.services.account_service": "the_alchemiser.services.account.legacy_account_service",
    "the_alchemiser.services.account_utils": "the_alchemiser.services.account.account_utils",
    "the_alchemiser.services.market_data_client": "the_alchemiser.services.market_data.market_data_client",
    "the_alchemiser.services.price_service": "the_alchemiser.services.market_data.price_service",
    "the_alchemiser.services.price_utils": "the_alchemiser.services.market_data.price_utils",
    "the_alchemiser.services.price_fetching_utils": "the_alchemiser.services.market_data.price_fetching_utils",
    "the_alchemiser.services.streaming_service": "the_alchemiser.services.market_data.streaming_service",
    "the_alchemiser.services.trading_client_service": "the_alchemiser.services.trading.trading_client_service",
    "the_alchemiser.services.position_manager": "the_alchemiser.services.trading.position_manager",
    "the_alchemiser.services.cache_manager": "the_alchemiser.services.shared.cache_manager",
    "the_alchemiser.services.config_service": "the_alchemiser.services.shared.config_service",
    "the_alchemiser.services.retry_decorator": "the_alchemiser.services.shared.retry_decorator",
    "the_alchemiser.services.secrets_service": "the_alchemiser.services.shared.secrets_service",
    "the_alchemiser.services.service_factory": "the_alchemiser.services.shared.service_factory",
    "the_alchemiser.services.alpaca_manager": "the_alchemiser.services.repository.alpaca_manager",
    # Errors
    "the_alchemiser.services.error_handler": "the_alchemiser.services.errors.error_handler",
    "the_alchemiser.services.error_handling": "the_alchemiser.services.errors.error_handling",
    "the_alchemiser.services.error_monitoring": "the_alchemiser.services.errors.error_monitoring",
    "the_alchemiser.services.error_recovery": "the_alchemiser.services.errors.error_recovery",
    "the_alchemiser.services.error_reporter": "the_alchemiser.services.errors.error_reporter",
    "the_alchemiser.services.exceptions": "the_alchemiser.services.errors.exceptions",
}

# Precompile regex patterns
# Matches: from <module> import ...
FROM_RE = re.compile(r"^(?P<indent>\s*)from\s+(?P<module>[\w\.]+)\s+import\s+", re.MULTILINE)
# Matches: import <module>( as alias)? or multiple modules comma separated
# We'll handle simple single-module imports safely.
IMPORT_RE = re.compile(
    r"^(?P<indent>\s*)import\s+(?P<module>[\w\.]+)(?P<rest>\s+as\s+\w+)?\s*$", re.MULTILINE
)

# Special handling for the old aggregator package
ENHANCED_FROM_RE = re.compile(
    r"^(?P<indent>\s*)from\s+the_alchemiser\.services\.enhanced\s+import\s+(?P<names>[^#\n]+)(?P<comment>\s*#.*)?$",
    re.MULTILINE,
)

# Symbol-to-module mapping for the old enhanced aggregator
ENHANCED_SYMBOL_MAP: dict[str, str] = {
    "TradingServiceManager": "the_alchemiser.services.trading.trading_service_manager",
    "AccountService": "the_alchemiser.services.account.account_service",
    "MarketDataService": "the_alchemiser.services.market_data.market_data_service",
    "OrderService": "the_alchemiser.services.trading.order_service",
    "OrderType": "the_alchemiser.services.trading.order_service",
    "OrderValidationError": "the_alchemiser.services.trading.order_service",
    "PositionService": "the_alchemiser.services.trading.position_service",
    "PositionValidationError": "the_alchemiser.services.trading.position_service",
    "PortfolioSummary": "the_alchemiser.services.trading.position_service",
    "PositionInfo": "the_alchemiser.services.trading.position_service",
}


@dataclass
class Change:
    path: Path
    original: str
    updated: str


def iter_python_files(root: Path) -> Iterable[Path]:
    skip_dirs = {".git", ".venv", "__pycache__", "htmlcov", "dist", "build", "node_modules"}
    for p in root.rglob("*.py"):
        if any(part in skip_dirs for part in p.parts):
            continue
        yield p


def rewrite_content(text: str) -> str:
    # Rewrite 'from the_alchemiser.services.enhanced import ...'
    def repl_from_enhanced(m: re.Match[str]) -> str:
        indent = m.group("indent")
        names_str = m.group("names")
        comment = m.group("comment") or ""
        parts = [p.strip() for p in names_str.split(",") if p.strip()]
        module_to_names: dict[str, list[str]] = {}
        unknown: list[str] = []

        for part in parts:
            # Support aliases: Name as Alias
            alias_match = re.match(r"^(?P<name>\w+)\s+as\s+(?P<alias>\w+)$", part)
            if alias_match:
                name = alias_match.group("name")
                alias = alias_match.group("alias")
            else:
                name = part
                alias = None

            target_module = ENHANCED_SYMBOL_MAP.get(name)
            if not target_module:
                unknown.append(part)
                continue
            rendered = f"{name} as {alias}" if alias else name
            module_to_names.setdefault(target_module, []).append(rendered)

        if unknown:
            # If there are unknowns, keep the original line to avoid breaking code
            return m.group(0)

        # Build grouped import lines
        lines = [
            f"{indent}from {mod} import {', '.join(names)}"
            for mod, names in module_to_names.items()
        ]
        if comment:
            # Attach trailing comment to the last line
            lines[-1] = lines[-1] + comment
        return "\n".join(lines)

    text = ENHANCED_FROM_RE.sub(repl_from_enhanced, text)

    # Handle 'from ... import'
    def repl_from(m: re.Match[str]) -> str:
        module = m.group("module")
        indent = m.group("indent")
        new_module = MODULE_MAP.get(module)
        if new_module:
            return f"{indent}from {new_module} import "
        # Also support prefix matches (e.g., from X.Y import Z)
        for old, new in MODULE_MAP.items():
            if module.startswith(old + "."):
                suffix = module[len(old) + 1 :]
                return f"{indent}from {new}.{suffix} import "
        return m.group(0)

    text = FROM_RE.sub(repl_from, text)

    # Handle 'import ...' single module per line
    def repl_import(m: re.Match[str]) -> str:
        module = m.group("module")
        rest = m.group("rest") or ""
        new_module = MODULE_MAP.get(module)
        if new_module:
            return f"import {new_module}{rest}"
        for old, new in MODULE_MAP.items():
            if module.startswith(old + "."):
                suffix = module[len(old) + 1 :]
                return f"import {new}.{suffix}{rest}"
        return m.group(0)

    text = IMPORT_RE.sub(repl_import, text)
    return text


def process_file(path: Path, apply: bool) -> Change | None:
    original = path.read_text(encoding="utf-8")
    updated = rewrite_content(original)
    if updated != original:
        if apply:
            path.write_text(updated, encoding="utf-8")
        return Change(path=path, original=original, updated=updated)
    return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Update imports after services reorg")
    parser.add_argument("--apply", action="store_true", help="Write changes to files")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args(argv)

    changes: list[Change] = []
    for py in iter_python_files(SRC_ROOT):
        ch = process_file(py, apply=args.apply)
        if ch:
            changes.append(ch)
            if args.verbose:
                print(f"updated: {py.relative_to(REPO_ROOT)}")

    print(
        f"{len(changes)} file(s) would be updated" + (" (applied)" if args.apply else " (dry-run)")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
