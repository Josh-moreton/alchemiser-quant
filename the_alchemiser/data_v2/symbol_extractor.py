"""Business Unit: data | Status: current.

Symbol extraction from DSL strategy files.

Parses DSL strategy configuration files and extracts all unique ticker symbols
referenced in asset declarations and indicator functions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Reserved keywords that should not be treated as ticker symbols
RESERVED_KEYWORDS = frozenset(
    {
        "TRUE",
        "FALSE",
        "AND",
        "OR",
        "IF",
        "ELSE",
        "NOT",
        "THEN",
        "NIL",
        "NULL",
        "NONE",
        "NAN",
        "INF",
    }
)

# Pattern to match ticker symbols in DSL files
# Matches quoted strings that look like tickers (1-6 uppercase letters)
TICKER_PATTERN = re.compile(r'"([A-Z]{1,6})"')

# Pattern to match asset declarations: (asset "SYMBOL" ...)
ASSET_PATTERN = re.compile(r'\(asset\s+"([A-Z]{1,6})"')

# Pattern to match indicator functions: (rsi "SYMBOL" ...), (cumulative-return "SYMBOL" ...), etc.
INDICATOR_PATTERNS = [
    re.compile(r'\(rsi\s+"([A-Z]{1,6})"'),
    re.compile(r'\(current-price\s+"([A-Z]{1,6})"'),
    re.compile(r'\(moving-average-price\s+"([A-Z]{1,6})"'),
    re.compile(r'\(moving-average-return\s+"([A-Z]{1,6})"'),
    re.compile(r'\(cumulative-return\s+"([A-Z]{1,6})"'),
    re.compile(r'\(exponential-moving-average-price\s+"([A-Z]{1,6})"'),
    re.compile(r'\(stdev-return\s+"([A-Z]{1,6})"'),
    re.compile(r'\(max-drawdown\s+"([A-Z]{1,6})"'),
    re.compile(r'\(volatility\s+"([A-Z]{1,6})"'),
]


def extract_symbols_from_file(file_path: Path) -> set[str]:
    """Extract all ticker symbols from a single DSL strategy file.

    Args:
        file_path: Path to the .clj strategy file

    Returns:
        Set of unique ticker symbols found in the file

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read

    """
    content = file_path.read_text(encoding="utf-8")
    symbols: set[str] = set()

    # Extract from asset declarations
    for match in ASSET_PATTERN.finditer(content):
        symbol = match.group(1)
        if symbol not in RESERVED_KEYWORDS:
            symbols.add(symbol)

    # Extract from indicator function calls
    for pattern in INDICATOR_PATTERNS:
        for match in pattern.finditer(content):
            symbol = match.group(1)
            if symbol not in RESERVED_KEYWORDS:
                symbols.add(symbol)

    logger.debug(
        "Extracted symbols from file",
        file_path=str(file_path),
        symbol_count=len(symbols),
    )

    return symbols


def extract_symbols_from_config(config_path: Path, strategies_dir: Path) -> set[str]:
    """Extract all symbols from strategies listed in a config file.

    Args:
        config_path: Path to strategy config JSON (e.g., strategy.dev.json)
        strategies_dir: Base directory containing strategy .clj files

    Returns:
        Set of unique ticker symbols across all configured strategies

    Raises:
        FileNotFoundError: If config file or strategy files don't exist
        json.JSONDecodeError: If config file is not valid JSON

    """
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    strategy_files = config.get("files", [])
    all_symbols: set[str] = set()

    for strategy_file in strategy_files:
        file_path = strategies_dir / strategy_file
        if file_path.exists():
            symbols = extract_symbols_from_file(file_path)
            all_symbols.update(symbols)
            logger.info(
                "Extracted symbols from strategy",
                strategy=strategy_file,
                symbol_count=len(symbols),
            )
        else:
            logger.warning(
                "Strategy file not found",
                strategy=strategy_file,
                path=str(file_path),
            )

    return all_symbols


def get_all_configured_symbols(base_path: Path | None = None) -> set[str]:
    """Get all symbols from both dev and prod strategy configurations.

    Args:
        base_path: Base path to the_alchemiser directory.
            If None, attempts to find it relative to this module.

    Returns:
        Set of all unique ticker symbols across all configured strategies

    """
    if base_path is None:
        # Resolve relative to this module's location
        base_path = Path(__file__).parent.parent

    config_dir = base_path / "config"
    strategies_dir = base_path / "strategy_v2" / "strategies"

    all_symbols: set[str] = set()

    # Process both dev and prod configs
    for config_name in ["strategy.dev.json", "strategy.prod.json"]:
        config_path = config_dir / config_name
        if config_path.exists():
            symbols = extract_symbols_from_config(config_path, strategies_dir)
            all_symbols.update(symbols)
            logger.info(
                "Processed config file",
                config=config_name,
                total_symbols=len(symbols),
            )
        else:
            logger.warning(
                "Config file not found",
                config=config_name,
                path=str(config_path),
            )

    logger.info(
        "Total unique symbols extracted",
        total=len(all_symbols),
        symbols=sorted(all_symbols),
    )

    return all_symbols
