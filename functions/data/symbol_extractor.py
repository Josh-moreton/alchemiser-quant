"""Business Unit: data | Status: current.

Symbol extraction from DSL strategy files.

Parses DSL strategy configuration files and extracts all unique ticker symbols
referenced in asset declarations and indicator functions.
"""

from __future__ import annotations

import json
import re
from importlib import resources as importlib_resources
from pathlib import Path
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from importlib.abc import Traversable

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
    re.compile(r'\(stdev-price\s+"([A-Z]{1,6})"'),
    re.compile(r'\(max-drawdown\s+"([A-Z]{1,6})"'),
    re.compile(r'\(volatility\s+"([A-Z]{1,6})"'),
]


def _extract_symbols_from_content(content: str) -> set[str]:
    """Extract ticker symbols from DSL file content.

    Args:
        content: DSL strategy file content

    Returns:
        Set of unique ticker symbols found in the content

    """
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

    return symbols


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
    symbols = _extract_symbols_from_content(content)

    logger.debug(
        "Extracted symbols from file",
        file_path=str(file_path),
        symbol_count=len(symbols),
    )

    return symbols


def extract_symbols_from_config(
    config_path: Traversable | Path,
    strategies_dir: Traversable | Path,
) -> set[str]:
    """Extract all symbols from strategies listed in a config file.

    Args:
        config_path: Path-like to strategy config JSON (e.g., strategy.dev.json)
        strategies_dir: Path-like to directory containing strategy .clj files

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
        try:
            if file_path.is_file():
                # Convert Traversable to Path for extract_symbols_from_file if needed
                if hasattr(file_path, "__fspath__"):
                    symbols = extract_symbols_from_file(Path(file_path))
                else:
                    # Read content directly from Traversable
                    content = file_path.read_text(encoding="utf-8")
                    symbols = _extract_symbols_from_content(content)

                all_symbols.update(symbols)
                logger.info(
                    "Extracted symbols from strategy",
                    strategy=strategy_file,
                    symbol_count=len(symbols),
                )
            else:
                # Fail loudly - missing strategy files indicate deployment/config issues
                logger.error(
                    "Strategy file not found - cannot extract symbols",
                    strategy=strategy_file,
                    path=str(file_path),
                )
                raise FileNotFoundError(
                    f"Strategy file not found: {strategy_file} at {file_path}"
                )
        except FileNotFoundError:
            # Re-raise file not found errors (don't swallow them)
            raise
        except Exception as e:
            # Fail loudly - extraction failures indicate malformed strategy files
            logger.error(
                "Failed to extract symbols from strategy - file may be malformed",
                strategy=strategy_file,
                error=str(e),
            )
            raise RuntimeError(
                f"Failed to extract symbols from strategy {strategy_file}: {e}"
            ) from e

    return all_symbols


def get_all_configured_symbols() -> set[str]:
    """Get all symbols from both dev and prod strategy configurations.

    Uses importlib.resources to locate files in the shared Lambda layer.

    Returns:
        Set of all unique ticker symbols across all configured strategies

    """
    all_symbols: set[str] = set()

    # Get paths using importlib.resources
    config_package = "the_alchemiser.shared.config"
    strategies_package = "the_alchemiser.shared.strategies"

    try:
        config_path = importlib_resources.files(config_package)
        strategies_path = importlib_resources.files(strategies_package)
    except (ModuleNotFoundError, AttributeError) as e:
        # Fail loudly - missing layer packages means deployment is broken
        # An empty symbol set would skip all data refresh, which is catastrophic
        logger.error(
            "Failed to locate shared layer packages - cannot extract symbols",
            error=str(e),
            config_package=config_package,
            strategies_package=strategies_package,
        )
        raise RuntimeError(
            f"Cannot locate shared layer packages ({config_package}, {strategies_package}): {e}"
        ) from e

    # Process both dev and prod configs
    configs_processed = 0
    config_errors: list[str] = []
    
    for config_name in ["strategy.dev.json", "strategy.prod.json"]:
        config_file = config_path / config_name
        try:
            if config_file.is_file():
                symbols = extract_symbols_from_config(config_file, strategies_path)
                all_symbols.update(symbols)
                configs_processed += 1
                logger.info(
                    "Processed config file",
                    config=config_name,
                    total_symbols=len(symbols),
                )
            else:
                # Log as error but continue - at least one config should exist
                error_msg = f"Config file not found: {config_name} at {config_file}"
                config_errors.append(error_msg)
                logger.error(
                    "Config file not found",
                    config=config_name,
                    path=str(config_file),
                )
        except Exception as e:
            # Fail loudly on config processing errors
            logger.error(
                "Failed to process config file",
                config=config_name,
                error=str(e),
            )
            raise RuntimeError(
                f"Failed to process config file {config_name}: {e}"
            ) from e

    # Ensure at least one config was processed successfully
    if configs_processed == 0:
        raise RuntimeError(
            f"No strategy config files found. Errors: {'; '.join(config_errors)}"
        )

    logger.info(
        "Total unique symbols extracted",
        total=len(all_symbols),
        symbols=sorted(all_symbols),
    )

    return all_symbols
