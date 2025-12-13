#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for order ID generation utilities.

Validates client_order_id generation and parsing functions.
"""

from __future__ import annotations

from the_alchemiser.shared.utils.order_id_utils import (
    generate_client_order_id,
    parse_client_order_id,
)


class TestGenerateClientOrderId:
    """Test client order ID generation."""

    def test_generates_valid_format(self) -> None:
        """Test that generated client_order_id has expected format."""
        client_order_id = generate_client_order_id("AAPL")
        parts = client_order_id.split("-")

        # Should have 4 parts: strategy-symbol-timestamp-uuid
        assert len(parts) == 4
        assert parts[0] == "alch"  # Default strategy
        assert parts[1] == "AAPL"  # Symbol
        assert len(parts[2]) == 15  # Timestamp (YYYYMMDDTHHmmss)
        assert len(parts[3]) == 8  # UUID suffix (first 8 chars)

    def test_custom_strategy(self) -> None:
        """Test client_order_id generation with custom strategy."""
        client_order_id = generate_client_order_id("TSLA", strategy="momentum")
        parts = client_order_id.split("-")

        assert parts[0] == "momentum"
        assert parts[1] == "TSLA"

    def test_custom_prefix(self) -> None:
        """Test client_order_id generation with custom prefix."""
        client_order_id = generate_client_order_id("NVDA", prefix="custom")
        parts = client_order_id.split("-")

        assert parts[0] == "custom"
        assert parts[1] == "NVDA"

    def test_prefix_overrides_strategy(self) -> None:
        """Test that prefix overrides strategy when both provided."""
        client_order_id = generate_client_order_id(
            "AAPL", strategy="momentum", prefix="override"
        )
        parts = client_order_id.split("-")

        assert parts[0] == "override"

    def test_normalizes_symbol(self) -> None:
        """Test that symbol is normalized to uppercase."""
        client_order_id = generate_client_order_id("aapl")
        parts = client_order_id.split("-")

        assert parts[1] == "AAPL"

    def test_handles_symbol_with_slash(self) -> None:
        """Test that symbols with slashes are handled correctly."""
        client_order_id = generate_client_order_id("BTC/USD")
        parts = client_order_id.split("-")

        # Slashes should be replaced with hyphens
        assert parts[1] == "BTC-USD"

    def test_uniqueness(self) -> None:
        """Test that consecutive calls generate unique IDs."""
        id1 = generate_client_order_id("AAPL")
        id2 = generate_client_order_id("AAPL")

        assert id1 != id2


class TestParseClientOrderId:
    """Test client order ID parsing."""

    def test_parses_valid_id(self) -> None:
        """Test parsing a valid client_order_id."""
        client_order_id = "alch-AAPL-20240115T093000-a1b2c3d4"
        result = parse_client_order_id(client_order_id)

        assert result is not None
        assert result["strategy"] == "alch"
        assert result["symbol"] == "AAPL"
        assert result["timestamp"] == "20240115T093000"
        assert result["uuid_suffix"] == "a1b2c3d4"

    def test_returns_none_for_invalid_format(self) -> None:
        """Test that invalid format returns None."""
        result = parse_client_order_id("invalid-format")

        assert result is None

    def test_returns_none_for_too_many_parts(self) -> None:
        """Test that too many parts returns None."""
        result = parse_client_order_id("alch-AAPL-20240115T093000-a1b2c3d4-extra")

        assert result is None

    def test_returns_none_for_too_few_parts(self) -> None:
        """Test that too few parts returns None."""
        result = parse_client_order_id("alch-AAPL")

        assert result is None

    def test_parses_custom_strategy(self) -> None:
        """Test parsing client_order_id with custom strategy."""
        client_order_id = "momentum-TSLA-20240115T093000-a1b2c3d4"
        result = parse_client_order_id(client_order_id)

        assert result is not None
        assert result["strategy"] == "momentum"


class TestRoundTrip:
    """Test round-trip generation and parsing."""

    def test_round_trip_default(self) -> None:
        """Test that generated ID can be parsed back."""
        generated_id = generate_client_order_id("AAPL")
        parsed = parse_client_order_id(generated_id)

        assert parsed is not None
        assert parsed["strategy"] == "alch"
        assert parsed["symbol"] == "AAPL"

    def test_round_trip_custom_strategy(self) -> None:
        """Test round-trip with custom strategy."""
        generated_id = generate_client_order_id("TSLA", strategy="momentum")
        parsed = parse_client_order_id(generated_id)

        assert parsed is not None
        assert parsed["strategy"] == "momentum"
        assert parsed["symbol"] == "TSLA"
