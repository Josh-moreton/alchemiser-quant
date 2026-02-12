"""Business Unit: shared | Status: current.

Client Order ID generation utilities for Alpaca order tracking.

Provides functions to generate unique, human-readable client order IDs
that enable better tracking and organization of orders across strategies.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

# Constants
LEGACY_STRATEGY_PREFIX = "alch"  # Legacy prefix for backward compatibility


def generate_client_order_id(
    symbol: str,
    strategy_id: str,
    *,
    prefix: str | None = None,
    signal_version: str | None = None,
) -> str:
    """Generate a unique client order ID for Alpaca order tracking.

    Creates a human-readable, unique client order ID that includes:
    - Strategy identifier (REQUIRED)
    - Trading symbol
    - Timestamp (for uniqueness and ordering)
    - Short UUID suffix (for guaranteed uniqueness)
    - Optional signal version (for replay correlation)

    Format: `{strategy_id}-{symbol}-{timestamp}-{uuid_suffix}[-v{version}]`

    Args:
        symbol: Trading symbol (e.g., 'AAPL', 'TSLA')
        strategy_id: Strategy identifier (e.g., 'nuclear', 'momentum', 'kmlm')
        prefix: Optional custom prefix to override strategy_id
        signal_version: Optional signal version for replay correlation (e.g., 'v1', '1')

    Returns:
        Unique client order ID string

    Raises:
        ValueError: If signal_version contains hyphens.

    Examples:
        >>> # Basic usage with strategy_id
        >>> client_order_id = generate_client_order_id("AAPL", "nuclear")
        >>> # Returns: "nuclear-AAPL-20250115T093000-a1b2c3d4"

        >>> # With signal version tracking
        >>> client_order_id = generate_client_order_id("TSLA", "momentum", signal_version="v1")
        >>> # Returns: "momentum-TSLA-20250115T093000-a1b2c3d4-v1"

        >>> # With custom prefix
        >>> client_order_id = generate_client_order_id("NVDA", "kmlm", prefix="custom")
        >>> # Returns: "custom-NVDA-20250115T093000-a1b2c3d4"

    Notes:
        - Client order IDs enable per-strategy order attribution
        - They enable multi-strategy P&L decomposition
        - The timestamp ensures chronological ordering
        - The UUID suffix guarantees uniqueness even for concurrent orders
        - Signal version enables correlation with signal generation events
        - Alpaca limits client_order_id to 48 characters
        - Long strategy_id/prefix values are auto-truncated to fit
        - Slashes in symbols (e.g., BTC/USD) are replaced with underscores

    """
    # Alpaca's maximum client_order_id length
    MAX_CLIENT_ORDER_ID_LENGTH = 48

    # Use prefix if provided, otherwise use strategy_id
    prefix_part = prefix if prefix is not None else strategy_id

    # Normalize symbol to uppercase and replace slashes with underscores
    # Using underscore instead of hyphen to preserve round-trip parsing
    normalized_symbol = symbol.strip().upper().replace("/", "_")

    # Generate timestamp in compact format (YYYYMMDDTHHmmss)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")

    # Generate short UUID suffix (first 8 characters)
    uuid_suffix = str(uuid.uuid4())[:8]

    # Calculate version suffix if provided
    version_suffix = ""
    if signal_version is not None:
        # Validate signal version doesn't contain hyphens (would break parsing)
        if "-" in signal_version:
            raise ValueError(
                f"signal_version cannot contain hyphens (breaks parsing): {signal_version}"
            )
        # Normalize version to have 'v' prefix if not present
        version_str = signal_version if signal_version.startswith("v") else f"v{signal_version}"
        version_suffix = f"-{version_str}"

    # Calculate fixed overhead: separators + symbol + timestamp + uuid + version
    fixed_length = (
        1 + len(normalized_symbol) + 1 + len(timestamp) + 1 + len(uuid_suffix) + len(version_suffix)
    )
    max_prefix_length = MAX_CLIENT_ORDER_ID_LENGTH - fixed_length

    # Guard: if symbol + timestamp + uuid + version already consumes the budget,
    # ensure we still produce a valid (non-empty) prefix and final ID <= 48 chars.
    if max_prefix_length <= 0:
        raise ValueError(
            f"Cannot build client_order_id: symbol '{normalized_symbol}' and fixed "
            f"fields consume {fixed_length} chars, exceeding the {MAX_CLIENT_ORDER_ID_LENGTH}-char limit. "
            f"Use a shorter symbol or omit signal_version."
        )

    # Auto-truncate prefix if it would exceed Alpaca's limit
    if len(prefix_part) > max_prefix_length:
        prefix_part = prefix_part[:max_prefix_length]

    # Final length validation (defensive)
    client_order_id = f"{prefix_part}-{normalized_symbol}-{timestamp}-{uuid_suffix}{version_suffix}"
    if len(client_order_id) > MAX_CLIENT_ORDER_ID_LENGTH:
        raise ValueError(
            f"Generated client_order_id exceeds {MAX_CLIENT_ORDER_ID_LENGTH} chars: "
            f"{len(client_order_id)} ('{client_order_id}')"
        )

    return client_order_id


def parse_client_order_id(client_order_id: str) -> dict[str, str | None] | None:
    """Parse a client order ID to extract components.

    Handles both legacy and new formats:
    - Legacy: alch-SYMBOL-TIMESTAMP-UUID (4 parts)
    - New: STRATEGY-SYMBOL-TIMESTAMP-UUID[-VERSION] (4 or 5 parts)

    .. note::
        **Status: Ready for Integration**

        This function is tested but not yet wired into production flows.
        It's designed as a fallback mechanism to extract strategy_id from
        client_order_id when rebalance plan metadata is unavailable
        (e.g., manual orders or pre-existing positions).

        Integration point: ``execution_v2/services/trade_ledger.py``
        in ``_extract_strategy_attribution()`` as fallback when
        ``rebalance_plan.metadata["strategy_attribution"]`` is missing.

    Args:
        client_order_id: Client order ID string to parse

    Returns:
        Dictionary with keys: 'strategy_id', 'symbol', 'timestamp', 'uuid_suffix', 'version'
        Returns None if the format is invalid

    Raises:
        This function does not raise exceptions.

    Examples:
        >>> # Legacy format
        >>> client_order_id = "alch-AAPL-20250115T093000-a1b2c3d4"
        >>> result = parse_client_order_id(client_order_id)
        >>> result
        {
            'strategy_id': 'unknown',  # Legacy marker
            'symbol': 'AAPL',
            'timestamp': '20250115T093000',
            'uuid_suffix': 'a1b2c3d4',
            'version': None
        }

        >>> # New format without version
        >>> client_order_id = "nuclear-AAPL-20250115T093000-a1b2c3d4"
        >>> result = parse_client_order_id(client_order_id)
        >>> result
        {
            'strategy_id': 'nuclear',
            'symbol': 'AAPL',
            'timestamp': '20250115T093000',
            'uuid_suffix': 'a1b2c3d4',
            'version': None
        }

        >>> # New format with version
        >>> client_order_id = "momentum-TSLA-20250115T093000-a1b2c3d4-v1"
        >>> result = parse_client_order_id(client_order_id)
        >>> result
        {
            'strategy_id': 'momentum',
            'symbol': 'TSLA',
            'timestamp': '20250115T093000',
            'uuid_suffix': 'a1b2c3d4',
            'version': 'v1'
        }

    """
    try:
        parts = client_order_id.split("-")

        # Must have at least 4 parts (strategy-symbol-timestamp-uuid)
        # May have 5 parts if version is included
        if len(parts) < 4 or len(parts) > 5:
            return None

        # Extract strategy_id - check if legacy prefix
        # NOTE: We intentionally treat LEGACY_STRATEGY_PREFIX ("alch") as a legacy marker
        # to distinguish old orders from new ones. If "alch" is needed as a strategy name
        # going forward, use a different name like "alchemy" or "alchemiser".
        strategy_id = parts[0]
        if strategy_id == LEGACY_STRATEGY_PREFIX:
            strategy_id = "unknown"  # Mark as legacy/unknown strategy

        # Extract version if present (5th part)
        version = parts[4] if len(parts) == 5 else None

        return {
            "strategy_id": strategy_id,
            "symbol": parts[1],
            "timestamp": parts[2],
            "uuid_suffix": parts[3],
            "version": version,
        }
    except (AttributeError, IndexError, ValueError):
        return None


__all__ = [
    "generate_client_order_id",
    "parse_client_order_id",
]
