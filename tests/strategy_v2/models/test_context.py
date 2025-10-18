#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Test suite for StrategyContext model.

Tests cover validation, immutability, normalization, and edge cases
for the strategy execution context model.
"""

from datetime import UTC, datetime, timedelta

import pytest

from the_alchemiser.strategy_v2.errors import ConfigurationError
from the_alchemiser.strategy_v2.models.context import StrategyContext


class TestStrategyContextValidation:
    """Test validation logic in StrategyContext."""

    def test_valid_context_creation(self):
        """Test creating a valid context."""
        context = StrategyContext(
            symbols=["AAPL", "MSFT"],
            timeframe="1D",
            as_of=datetime.now(UTC),
            params={"threshold": 0.5, "lookback": 30},
        )
        assert context.symbols == ["AAPL", "MSFT"]
        assert context.timeframe == "1D"
        assert context.as_of is not None
        assert context.params is not None

    def test_empty_symbols_raises_error(self):
        """Test that empty symbols list raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="symbols cannot be empty"):
            StrategyContext(symbols=[], timeframe="1D")

    def test_empty_timeframe_raises_error(self):
        """Test that empty timeframe raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="timeframe cannot be empty"):
            StrategyContext(symbols=["AAPL"], timeframe="")

    def test_symbols_normalized_to_uppercase(self):
        """Test that symbols are normalized to uppercase."""
        context = StrategyContext(symbols=["aapl", "MsFt", "GOOGL"], timeframe="1D")
        assert context.symbols == ["AAPL", "MSFT", "GOOGL"]

    def test_duplicate_symbols_case_insensitive_raises_error(self):
        """Test that duplicate symbols (case-insensitive) raise error."""
        with pytest.raises(
            ConfigurationError, match="symbols must be unique \\(case-insensitive\\)"
        ):
            StrategyContext(symbols=["AAPL", "aapl", "MSFT"], timeframe="1D")

    def test_duplicate_symbols_exact_raises_error(self):
        """Test that duplicate symbols raise error."""
        with pytest.raises(
            ConfigurationError, match="symbols must be unique \\(case-insensitive\\)"
        ):
            StrategyContext(symbols=["AAPL", "AAPL"], timeframe="1D")


class TestStrategyContextDefaults:
    """Test default values in StrategyContext."""

    def test_as_of_defaults_to_none(self):
        """Test that as_of defaults to None."""
        context = StrategyContext(symbols=["AAPL"], timeframe="1D")
        assert context.as_of is None

    def test_params_defaults_to_none(self):
        """Test that params defaults to None."""
        context = StrategyContext(symbols=["AAPL"], timeframe="1D")
        assert context.params is None


class TestStrategyContextImmutability:
    """Test immutability of StrategyContext."""

    def test_context_is_frozen(self):
        """Test that context attributes cannot be modified."""
        context = StrategyContext(symbols=["AAPL"], timeframe="1D")
        with pytest.raises(AttributeError):
            context.symbols = ["MSFT"]  # type: ignore
        with pytest.raises(AttributeError):
            context.timeframe = "1H"  # type: ignore

    def test_symbols_list_is_immutable_semantically(self):
        """Test that modifying symbols list doesn't affect context.

        Note: Python lists are mutable, but we expect users to treat
        the context as immutable. This test documents the limitation.
        """
        symbols = ["AAPL", "MSFT"]
        context = StrategyContext(symbols=symbols, timeframe="1D")

        # Original list still contains lowercase, but context has uppercase
        assert symbols == ["AAPL", "MSFT"]
        assert context.symbols == ["AAPL", "MSFT"]

        # Modifying original list doesn't affect context
        # (because new list is created in __post_init__)
        symbols.append("GOOGL")
        assert context.symbols == ["AAPL", "MSFT"]


class TestStrategyContextTimeframe:
    """Test timeframe validation and handling."""

    def test_valid_timeframe_formats(self):
        """Test various valid timeframe formats."""
        valid_timeframes = ["1Min", "5Min", "15Min", "1H", "4H", "1D", "1W", "1M"]
        for tf in valid_timeframes:
            context = StrategyContext(symbols=["AAPL"], timeframe=tf)
            assert context.timeframe == tf

    def test_timeframe_preserves_case(self):
        """Test that timeframe case is preserved."""
        context = StrategyContext(symbols=["AAPL"], timeframe="1d")
        assert context.timeframe == "1d"


class TestStrategyContextAsOf:
    """Test as_of timestamp handling."""

    def test_as_of_with_timezone_aware_datetime(self):
        """Test as_of with timezone-aware datetime."""
        now = datetime.now(UTC)
        context = StrategyContext(symbols=["AAPL"], timeframe="1D", as_of=now)
        assert context.as_of == now
        assert context.as_of.tzinfo is not None

    def test_as_of_with_past_datetime(self):
        """Test as_of with past datetime."""
        past = datetime.now(UTC) - timedelta(days=7)
        context = StrategyContext(symbols=["AAPL"], timeframe="1D", as_of=past)
        assert context.as_of == past

    def test_as_of_with_future_datetime(self):
        """Test as_of with future datetime (should be allowed for backtesting)."""
        future = datetime.now(UTC) + timedelta(days=1)
        context = StrategyContext(symbols=["AAPL"], timeframe="1D", as_of=future)
        assert context.as_of == future


class TestStrategyContextParams:
    """Test params field handling."""

    def test_params_with_various_types(self):
        """Test params with different value types."""
        params = {
            "string_param": "value",
            "int_param": 42,
            "float_param": 3.14,
            "bool_param": True,
        }
        context = StrategyContext(symbols=["AAPL"], timeframe="1D", params=params)
        assert context.params == params

    def test_params_with_empty_dict(self):
        """Test params with empty dictionary."""
        context = StrategyContext(symbols=["AAPL"], timeframe="1D", params={})
        assert context.params == {}


class TestStrategyContextEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_symbol(self):
        """Test context with single symbol."""
        context = StrategyContext(symbols=["AAPL"], timeframe="1D")
        assert len(context.symbols) == 1
        assert context.symbols == ["AAPL"]

    def test_many_symbols(self):
        """Test context with many symbols."""
        symbols = [f"SYM{i}" for i in range(100)]
        context = StrategyContext(symbols=symbols, timeframe="1D")
        assert len(context.symbols) == 100
        assert all(s.startswith("SYM") for s in context.symbols)

    def test_symbols_order_preserved(self):
        """Test that symbols order is preserved."""
        symbols = ["TSLA", "AAPL", "MSFT", "GOOGL"]
        context = StrategyContext(symbols=symbols, timeframe="1D")
        assert context.symbols == symbols

    def test_whitespace_in_timeframe_preserved(self):
        """Test that whitespace in timeframe is preserved."""
        # This is technically invalid but we don't validate format
        context = StrategyContext(symbols=["AAPL"], timeframe=" 1D ")
        assert context.timeframe == " 1D "


class TestStrategyContextRepresentation:
    """Test string representation and debugging."""

    def test_repr_includes_key_fields(self):
        """Test that repr includes important fields."""
        context = StrategyContext(symbols=["AAPL", "MSFT"], timeframe="1D")
        repr_str = repr(context)
        assert "StrategyContext" in repr_str
        assert "AAPL" in repr_str or "symbols" in repr_str
        assert "1D" in repr_str or "timeframe" in repr_str

    def test_str_representation(self):
        """Test string representation."""
        context = StrategyContext(symbols=["AAPL"], timeframe="1D")
        str_rep = str(context)
        # Dataclass provides default str which is same as repr
        assert len(str_rep) > 0
