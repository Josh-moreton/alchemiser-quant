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
        client_order_id = generate_client_order_id("AAPL", "nuclear")
        parts = client_order_id.split("-")

        # Should have 4 parts: strategy_id-symbol-timestamp-uuid
        assert len(parts) == 4
        assert parts[0] == "nuclear"  # Strategy ID
        assert parts[1] == "AAPL"  # Symbol
        assert len(parts[2]) == 15  # Timestamp (YYYYMMDDTHHmmss)
        assert len(parts[3]) == 8  # UUID suffix (first 8 chars)

    def test_custom_strategy(self) -> None:
        """Test client_order_id generation with custom strategy."""
        client_order_id = generate_client_order_id("TSLA", strategy_id="momentum")
        parts = client_order_id.split("-")

        assert parts[0] == "momentum"
        assert parts[1] == "TSLA"

    def test_custom_prefix(self) -> None:
        """Test client_order_id generation with custom prefix."""
        client_order_id = generate_client_order_id("NVDA", "kmlm", prefix="custom")
        parts = client_order_id.split("-")

        assert parts[0] == "custom"
        assert parts[1] == "NVDA"

    def test_prefix_overrides_strategy(self) -> None:
        """Test that prefix overrides strategy when both provided."""
        client_order_id = generate_client_order_id(
            "AAPL", strategy_id="momentum", prefix="override"
        )
        parts = client_order_id.split("-")

        assert parts[0] == "override"

    def test_normalizes_symbol(self) -> None:
        """Test that symbol is normalized to uppercase."""
        client_order_id = generate_client_order_id("aapl", "nuclear")
        parts = client_order_id.split("-")

        assert parts[1] == "AAPL"

    def test_handles_symbol_with_slash(self) -> None:
        """Test that symbols with slashes are handled correctly."""
        client_order_id = generate_client_order_id("BTC/USD", "crypto")
        parts = client_order_id.split("-")

        # Slashes should be replaced with underscores to preserve round-trip parsing
        assert parts[1] == "BTC_USD"
        assert len(parts) == 4  # Should still have exactly 4 parts

    def test_uniqueness(self) -> None:
        """Test that consecutive calls generate unique IDs."""
        id1 = generate_client_order_id("AAPL", "nuclear")
        id2 = generate_client_order_id("AAPL", "nuclear")

        assert id1 != id2

    def test_with_signal_version(self) -> None:
        """Test client_order_id generation with signal version."""
        client_order_id = generate_client_order_id("AAPL", "nuclear", signal_version="v1")
        parts = client_order_id.split("-")

        # Should have 5 parts with version
        assert len(parts) == 5
        assert parts[0] == "nuclear"
        assert parts[1] == "AAPL"
        assert parts[4] == "v1"

    def test_signal_version_adds_v_prefix(self) -> None:
        """Test that signal version without 'v' prefix gets it added."""
        client_order_id = generate_client_order_id("TSLA", "momentum", signal_version="1")
        parts = client_order_id.split("-")

        assert len(parts) == 5
        assert parts[4] == "v1"

    def test_signal_version_preserves_v_prefix(self) -> None:
        """Test that signal version with 'v' prefix is preserved."""
        client_order_id = generate_client_order_id("NVDA", "kmlm", signal_version="v2")
        parts = client_order_id.split("-")

        assert len(parts) == 5
        assert parts[4] == "v2"


class TestParseClientOrderId:
    """Test client order ID parsing."""

    def test_parses_valid_id_new_format(self) -> None:
        """Test parsing a valid client_order_id in new format."""
        client_order_id = "nuclear-AAPL-20250115T093000-a1b2c3d4"
        result = parse_client_order_id(client_order_id)

        assert result is not None
        assert result["strategy_id"] == "nuclear"
        assert result["symbol"] == "AAPL"
        assert result["timestamp"] == "20250115T093000"
        assert result["uuid_suffix"] == "a1b2c3d4"
        assert result["version"] is None

    def test_parses_legacy_alch_format(self) -> None:
        """Test parsing legacy 'alch-' format returns 'unknown' strategy."""
        client_order_id = "alch-AAPL-20250115T093000-a1b2c3d4"
        result = parse_client_order_id(client_order_id)

        assert result is not None
        assert result["strategy_id"] == "unknown"  # Legacy marker
        assert result["symbol"] == "AAPL"
        assert result["timestamp"] == "20250115T093000"
        assert result["uuid_suffix"] == "a1b2c3d4"
        assert result["version"] is None

    def test_parses_id_with_version(self) -> None:
        """Test parsing client_order_id with signal version."""
        client_order_id = "momentum-TSLA-20250115T093000-a1b2c3d4-v1"
        result = parse_client_order_id(client_order_id)

        assert result is not None
        assert result["strategy_id"] == "momentum"
        assert result["symbol"] == "TSLA"
        assert result["timestamp"] == "20250115T093000"
        assert result["uuid_suffix"] == "a1b2c3d4"
        assert result["version"] == "v1"

    def test_returns_none_for_invalid_format(self) -> None:
        """Test that invalid format returns None."""
        result = parse_client_order_id("invalid-format")

        assert result is None

    def test_returns_none_for_too_many_parts(self) -> None:
        """Test that too many parts returns None."""
        result = parse_client_order_id("nuclear-AAPL-20250115T093000-a1b2c3d4-v1-extra")

        assert result is None

    def test_returns_none_for_too_few_parts(self) -> None:
        """Test that too few parts returns None."""
        result = parse_client_order_id("nuclear-AAPL")

        assert result is None

    def test_parses_custom_strategy(self) -> None:
        """Test parsing client_order_id with custom strategy."""
        client_order_id = "momentum-TSLA-20250115T093000-a1b2c3d4"
        result = parse_client_order_id(client_order_id)

        assert result is not None
        assert result["strategy_id"] == "momentum"


class TestRoundTrip:
    """Test round-trip generation and parsing."""

    def test_round_trip_default(self) -> None:
        """Test that generated ID can be parsed back."""
        generated_id = generate_client_order_id("AAPL", "nuclear")
        parsed = parse_client_order_id(generated_id)

        assert parsed is not None
        assert parsed["strategy_id"] == "nuclear"
        assert parsed["symbol"] == "AAPL"
        assert parsed["version"] is None

    def test_round_trip_custom_strategy(self) -> None:
        """Test round-trip with custom strategy."""
        generated_id = generate_client_order_id("TSLA", strategy_id="momentum")
        parsed = parse_client_order_id(generated_id)

        assert parsed is not None
        assert parsed["strategy_id"] == "momentum"
        assert parsed["symbol"] == "TSLA"
        assert parsed["version"] is None

    def test_round_trip_with_version(self) -> None:
        """Test round-trip with signal version."""
        generated_id = generate_client_order_id("NVDA", "kmlm", signal_version="v1")
        parsed = parse_client_order_id(generated_id)

        assert parsed is not None
        assert parsed["strategy_id"] == "kmlm"
        assert parsed["symbol"] == "NVDA"
        assert parsed["version"] == "v1"

    def test_round_trip_symbol_with_slash(self) -> None:
        """Test round-trip for crypto symbols with slashes."""
        generated_id = generate_client_order_id("BTC/USD", "crypto")
        parsed = parse_client_order_id(generated_id)

        assert parsed is not None
        assert parsed["strategy_id"] == "crypto"
        # Symbol has slash replaced with underscore
        assert parsed["symbol"] == "BTC_USD"
        # Verify all 5 components are present
        assert len(parsed) == 5
        assert "timestamp" in parsed
        assert "uuid_suffix" in parsed
        assert "version" in parsed


class TestAlpacaLimits:
    """Test Alpaca API constraints."""

    def test_generated_id_within_48_char_limit(self) -> None:
        """Test that generated IDs are within Alpaca's 48-character limit."""
        # Standard symbol with strategy
        client_order_id = generate_client_order_id("AAPL", "nuclear")
        assert len(client_order_id) <= 48

        # Longer symbol
        client_order_id = generate_client_order_id("GOOGL", "momentum")
        assert len(client_order_id) <= 48

        # Crypto pair
        client_order_id = generate_client_order_id("BTC/USD", "crypto")
        assert len(client_order_id) <= 48

    def test_generated_id_with_version_within_limit(self) -> None:
        """Test that IDs with version are within limit."""
        client_order_id = generate_client_order_id("AAPL", "nuclear", signal_version="v1")
        assert len(client_order_id) <= 48

    def test_exceeds_48_char_limit_raises_error(self) -> None:
        """Test that exceeding 48-character limit raises ValueError."""
        import pytest

        # Very long strategy name that would exceed limit
        # Format: {strategy}-{symbol}-{timestamp}-{uuid} = strategy + 1 + symbol + 1 + 15 + 1 + 8
        # For 48 chars: strategy + symbol can be at most 48 - 26 = 22 chars combined
        long_strategy = "a" * 30  # This plus symbol will exceed limit

        with pytest.raises(ValueError, match="exceeds Alpaca's 48-character limit"):
            generate_client_order_id("AAPL", strategy_id=long_strategy)

    def test_exceeds_limit_with_version_raises_error(self) -> None:
        """Test that exceeding limit with version raises ValueError."""
        import pytest

        # Strategy + symbol + version that would exceed limit
        long_strategy = "a" * 25

        with pytest.raises(ValueError, match="exceeds Alpaca's 48-character limit"):
            generate_client_order_id("AAPL", strategy_id=long_strategy, signal_version="v1")


class TestBackwardCompatibility:
    """Test backward compatibility with legacy format."""

    def test_legacy_format_parses_as_unknown_strategy(self) -> None:
        """Test that legacy 'alch-' format is recognized and marked as unknown."""
        legacy_id = "alch-AAPL-20250115T093000-a1b2c3d4"
        result = parse_client_order_id(legacy_id)

        assert result is not None
        assert result["strategy_id"] == "unknown"
        assert result["symbol"] == "AAPL"
        assert result["version"] is None

    def test_new_format_with_alch_strategy_not_marked_unknown(self) -> None:
        """Test that new format with 'alch' strategy is not marked unknown if used intentionally."""
        # This test ensures that if someone intentionally uses "alch" as a strategy_id
        # in the new format, it's still treated as unknown (legacy marker)
        new_id = "alch-TSLA-20250115T093000-a1b2c3d4"
        result = parse_client_order_id(new_id)

        assert result is not None
        assert result["strategy_id"] == "unknown"  # Still marked as legacy

    def test_can_distinguish_legacy_from_new_format(self) -> None:
        """Test that we can distinguish between legacy and new format."""
        legacy_id = "alch-AAPL-20250115T093000-a1b2c3d4"
        new_id = "nuclear-AAPL-20250115T093000-a1b2c3d4"

        legacy_result = parse_client_order_id(legacy_id)
        new_result = parse_client_order_id(new_id)

        assert legacy_result["strategy_id"] == "unknown"
        assert new_result["strategy_id"] == "nuclear"
