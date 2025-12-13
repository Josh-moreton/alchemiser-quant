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
        ValueError: If the generated ID exceeds Alpaca's 48-character limit.

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

    # Construct client order ID
    client_order_id = f"{prefix_part}-{normalized_symbol}-{timestamp}-{uuid_suffix}"

    # Add signal version if provided
    if signal_version is not None:
        # Validate signal version doesn't contain hyphens (would break parsing)
        if "-" in signal_version:
            raise ValueError(
                f"signal_version cannot contain hyphens (breaks parsing): {signal_version}"
            )
        # Normalize version to have 'v' prefix if not present
        version_str = signal_version if signal_version.startswith("v") else f"v{signal_version}"
        client_order_id = f"{client_order_id}-{version_str}"

    # Validate length against Alpaca's limit
    if len(client_order_id) > MAX_CLIENT_ORDER_ID_LENGTH:
        raise ValueError(
            f"Generated client_order_id exceeds Alpaca's {MAX_CLIENT_ORDER_ID_LENGTH}-character limit: "
            f"{len(client_order_id)} characters. Consider using shorter strategy_id/prefix, symbol, "
            "or signal_version."
        )

    return client_order_id


def parse_client_order_id(client_order_id: str) -> dict[str, str | None] | None:
    """Parse a client order ID to extract components.

    Handles both legacy and new formats:
    - Legacy: alch-SYMBOL-TIMESTAMP-UUID (4 parts)
    - New: STRATEGY-SYMBOL-TIMESTAMP-UUID[-VERSION] (4 or 5 parts)

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
