"""Business Unit: shared | Status: current.

Client Order ID generation utilities for Alpaca order tracking.

Provides functions to generate unique, human-readable client order IDs
that enable better tracking and organization of orders across strategies.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime


def generate_client_order_id(
    symbol: str,
    strategy: str = "alch",
    *,
    prefix: str | None = None,
) -> str:
    """Generate a unique client order ID for Alpaca order tracking.

    Creates a human-readable, unique client order ID that includes:
    - Strategy identifier (default: "alch")
    - Trading symbol
    - Timestamp (for uniqueness and ordering)
    - Short UUID suffix (for guaranteed uniqueness)

    Format: `{strategy}-{symbol}-{timestamp}-{uuid_suffix}`

    Args:
        symbol: Trading symbol (e.g., 'AAPL', 'TSLA')
        strategy: Strategy identifier (default: 'alch')
        prefix: Optional custom prefix to override strategy

    Returns:
        Unique client order ID string

    Raises:
        This function does not raise exceptions.

    Examples:
        >>> # Basic usage
        >>> client_order_id = generate_client_order_id("AAPL")
        >>> # Returns: "alch-AAPL-20240115T093000-a1b2c3d4"

        >>> # With custom strategy
        >>> client_order_id = generate_client_order_id("TSLA", strategy="momentum")
        >>> # Returns: "momentum-TSLA-20240115T093000-a1b2c3d4"

        >>> # With custom prefix
        >>> client_order_id = generate_client_order_id("NVDA", prefix="custom")
        >>> # Returns: "custom-NVDA-20240115T093000-a1b2c3d4"

    Notes:
        - Client order IDs are useful for tracking orders across strategies
        - They enable better organization in Alpaca's order management
        - The timestamp ensures chronological ordering
        - The UUID suffix guarantees uniqueness even for concurrent orders

    """
    # Use prefix if provided, otherwise use strategy
    prefix_part = prefix if prefix is not None else strategy

    # Normalize symbol to uppercase and remove any special characters
    normalized_symbol = symbol.strip().upper().replace("/", "-")

    # Generate timestamp in compact format (YYYYMMDDTHHmmss)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")

    # Generate short UUID suffix (first 8 characters)
    uuid_suffix = str(uuid.uuid4())[:8]

    # Construct client order ID
    return f"{prefix_part}-{normalized_symbol}-{timestamp}-{uuid_suffix}"


def parse_client_order_id(client_order_id: str) -> dict[str, str] | None:
    """Parse a client order ID to extract components.

    Args:
        client_order_id: Client order ID string to parse

    Returns:
        Dictionary with keys: 'strategy', 'symbol', 'timestamp', 'uuid_suffix'
        Returns None if the format is invalid

    Raises:
        This function does not raise exceptions.

    Examples:
        >>> client_order_id = "alch-AAPL-20240115T093000-a1b2c3d4"
        >>> result = parse_client_order_id(client_order_id)
        >>> result
        {
            'strategy': 'alch',
            'symbol': 'AAPL',
            'timestamp': '20240115T093000',
            'uuid_suffix': 'a1b2c3d4'
        }

    """
    try:
        parts = client_order_id.split("-")
        if len(parts) != 4:
            return None

        return {
            "strategy": parts[0],
            "symbol": parts[1],
            "timestamp": parts[2],
            "uuid_suffix": parts[3],
        }
    except (AttributeError, IndexError, ValueError):
        return None


__all__ = [
    "generate_client_order_id",
    "parse_client_order_id",
]
