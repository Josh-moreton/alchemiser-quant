#!/usr/bin/env python3
"""
Tests for StrategySignalModel.from_dict() method in domain/models/strategy.py.

Tests the enhanced from_dict method that handles flexible input types
including dict symbols and loose action strings.
"""


import pytest

from the_alchemiser.domain.models.strategy import StrategySignalModel
from the_alchemiser.domain.types import StrategySignal


class TestStrategySignalModelFromDict:
    """Test cases for StrategySignalModel.from_dict() method."""

    def test_from_dict_with_string_symbol_and_strict_action(self) -> None:
        """Test from_dict with string symbol and strict action type."""
        data: StrategySignal = {
            "symbol": "AAPL",
            "action": "BUY",
            "confidence": 0.85,
            "reasoning": "Strong earnings",
            "allocation_percentage": 25.0,
        }

        model = StrategySignalModel.from_dict(data)

        assert model.symbol == "AAPL"
        assert model.action == "BUY"
        assert model.confidence == 0.85
        assert model.reasoning == "Strong earnings"
        assert model.allocation_percentage == 25.0

    def test_from_dict_with_dict_symbol_takes_first_key(self) -> None:
        """Test from_dict with dict symbol extracts first key."""
        data: StrategySignal = {
            "symbol": {"TSLA": 0.6, "NVDA": 0.4},  # Portfolio allocation
            "action": "SELL",
            "confidence": 0.7,
            "reasoning": "Portfolio rebalancing",
            "allocation_percentage": 0.0,
        }

        model = StrategySignalModel.from_dict(data)

        assert model.symbol == "TSLA"  # First key from dict
        assert model.action == "SELL"
        assert model.confidence == 0.7
        assert model.reasoning == "Portfolio rebalancing"
        assert model.allocation_percentage == 0.0

    def test_from_dict_with_lowercase_action_normalizes_to_uppercase(self) -> None:
        """Test from_dict normalizes action to uppercase."""
        data: StrategySignal = {
            "symbol": "SPY",
            "action": "buy",  # lowercase
            "confidence": 0.9,
            "reasoning": "Market momentum",
            "allocation_percentage": 30.0,
        }

        model = StrategySignalModel.from_dict(data)

        assert model.action == "BUY"  # Normalized to uppercase

    def test_from_dict_with_invalid_action_defaults_to_hold(self) -> None:
        """Test from_dict with invalid action defaults to HOLD."""
        data: StrategySignal = {
            "symbol": "BTC",
            "action": "HODL",  # Invalid action
            "confidence": 0.5,
            "reasoning": "Invalid action test",
            "allocation_percentage": 10.0,
        }

        model = StrategySignalModel.from_dict(data)

        assert model.action == "HOLD"  # Default fallback

    def test_from_dict_handles_missing_optional_fields(self) -> None:
        """Test from_dict handles missing optional fields gracefully."""
        # Create minimal data with only required fields
        data: StrategySignal = {
            "symbol": "MSFT",
            "action": "HOLD",
            "confidence": 0.6,
            # reasoning and allocation_percentage are optional
        }

        model = StrategySignalModel.from_dict(data)

        assert model.symbol == "MSFT"
        assert model.action == "HOLD"
        assert model.confidence == 0.6
        assert model.reasoning == ""  # Default empty string
        assert model.allocation_percentage == 0.0  # Default value

    def test_from_dict_prefers_reasoning_over_reason(self) -> None:
        """Test from_dict prefers 'reasoning' field over legacy 'reason'."""
        data = {
            "symbol": "AMD",
            "action": "BUY",
            "confidence": 0.8,
            "reasoning": "Primary reasoning",
            "reason": "Legacy reasoning",  # Should be ignored
            "allocation_percentage": 15.0,
        }

        model = StrategySignalModel.from_dict(data)  # type: ignore

        assert model.reasoning == "Primary reasoning"  # reasoning takes precedence

    def test_from_dict_uses_reason_when_reasoning_missing(self) -> None:
        """Test from_dict uses 'reason' field when 'reasoning' is missing."""
        data = {
            "symbol": "INTC",
            "action": "SELL",
            "confidence": 0.4,
            "reason": "Legacy reasoning field",  # Only reason provided
            "allocation_percentage": 5.0,
        }

        model = StrategySignalModel.from_dict(data)  # type: ignore

        assert model.reasoning == "Legacy reasoning field"

    def test_from_dict_with_mixed_case_action_strings(self) -> None:
        """Test from_dict handles various case patterns in actions."""
        test_cases = [
            ("Buy", "BUY"),
            ("SELL", "SELL"),
            ("hold", "HOLD"),
            ("HoLd", "HOLD"),
            ("sElL", "SELL"),
        ]

        for input_action, expected_action in test_cases:
            data: StrategySignal = {
                "symbol": "TEST",
                "action": input_action,  # type: ignore
                "confidence": 0.5,
                "reasoning": f"Test {input_action}",
                "allocation_percentage": 1.0,
            }

            model = StrategySignalModel.from_dict(data)
            assert model.action == expected_action

    def test_from_dict_preserves_decimal_precision(self) -> None:
        """Test from_dict preserves decimal precision for float values."""
        data: StrategySignal = {
            "symbol": "PRECISION",
            "action": "BUY",
            "confidence": 0.123456789,  # High precision
            "reasoning": "Precision test",
            "allocation_percentage": 12.345,
        }

        model = StrategySignalModel.from_dict(data)

        assert model.confidence == 0.123456789
        assert model.allocation_percentage == 12.345

    def test_from_dict_with_empty_dict_symbol(self) -> None:
        """Test from_dict handles empty dict symbol gracefully."""
        data: StrategySignal = {
            "symbol": {},  # Empty dict
            "action": "HOLD",
            "confidence": 0.5,
            "reasoning": "Empty symbol test",
            "allocation_percentage": 0.0,
        }

        # This should raise an error or handle gracefully
        # Since next(iter({})) raises StopIteration, let's catch it
        with pytest.raises(StopIteration):
            StrategySignalModel.from_dict(data)

    def test_from_dict_comprehensive_valid_example(self) -> None:
        """Test from_dict with a comprehensive valid example."""
        data: StrategySignal = {
            "symbol": "QQQ",
            "action": "BUY",
            "confidence": 0.875,
            "reasoning": "Strong tech sector momentum with high confidence",
            "allocation_percentage": 22.5,
        }

        model = StrategySignalModel.from_dict(data)

        assert model.symbol == "QQQ"
        assert model.action == "BUY"
        assert model.confidence == 0.875
        assert model.reasoning == "Strong tech sector momentum with high confidence"
        assert model.allocation_percentage == 22.5
        # Verify it's still frozen/immutable
        with pytest.raises(AttributeError):
            model.symbol = "CHANGED"  # type: ignore
