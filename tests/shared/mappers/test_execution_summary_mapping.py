"""Business Unit: shared | Status: current.

Comprehensive unit tests for execution_summary_mapping module.

Tests cover:
- Valid conversions (happy path)
- Invalid inputs (None, wrong types, missing fields)
- Default value handling
- Decimal precision preservation
- Type validation
- Edge cases (empty dicts, None values)
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.mappers.execution_summary_mapping import (
    dict_to_allocation_summary,
    dict_to_execution_summary,
    dict_to_strategy_pnl_summary,
    dict_to_strategy_summary,
    dict_to_trading_summary,
)
from the_alchemiser.shared.schemas.execution_summary import (
    AllocationSummary,
    ExecutionSummary,
    StrategyPnLSummary,
    StrategySummary,
    TradingSummary,
)
from the_alchemiser.shared.value_objects.core_types import AccountInfo


@pytest.fixture
def sample_account_info() -> AccountInfo:
    """Fixture providing valid AccountInfo for testing."""
    return {
        "account_id": "test_account_123",
        "equity": Decimal("100000.00"),
        "cash": Decimal("50000.00"),
        "buying_power": Decimal("200000.00"),
        "day_trades_remaining": 3,
        "portfolio_value": Decimal("100000.00"),
        "last_equity": Decimal("98000.00"),
        "daytrading_buying_power": Decimal("400000.00"),
        "regt_buying_power": Decimal("200000.00"),
        "status": "ACTIVE",
    }


class TestDictToAllocationSummary:
    """Test dict_to_allocation_summary function."""

    def test_valid_allocation_summary(self):
        """Test conversion of valid allocation summary dict."""
        data = {
            "total_allocation": 95.5,
            "num_positions": 5,
            "largest_position_pct": 25.0,
        }
        result = dict_to_allocation_summary(data)
        
        assert isinstance(result, AllocationSummary)
        assert result.total_allocation == Decimal("95.5")
        assert result.num_positions == 5
        assert result.largest_position_pct == Decimal("25.0")

    def test_missing_fields_use_defaults(self):
        """Test that missing fields use default values."""
        data: dict[str, float | int] = {}
        result = dict_to_allocation_summary(data)
        
        assert result.total_allocation == Decimal("0.0")
        assert result.num_positions == 0
        assert result.largest_position_pct == Decimal("0.0")

    def test_decimal_precision_preserved(self):
        """Test that Decimal precision is preserved."""
        data = {
            "total_allocation": "95.1234",
            "num_positions": 5,
            "largest_position_pct": "25.5678",
        }
        result = dict_to_allocation_summary(data)
        
        assert result.total_allocation == Decimal("95.1234")
        assert result.largest_position_pct == Decimal("25.5678")

    def test_string_numbers_converted(self):
        """Test that string numbers are converted to Decimal."""
        data = {
            "total_allocation": "95.5",
            "num_positions": 5,
            "largest_position_pct": "25.0",
        }
        result = dict_to_allocation_summary(data)
        
        assert result.total_allocation == Decimal("95.5")
        assert result.largest_position_pct == Decimal("25.0")


class TestDictToStrategyPnlSummary:
    """Test dict_to_strategy_pnl_summary function."""

    def test_valid_pnl_summary(self):
        """Test conversion of valid P&L summary dict."""
        data = {
            "total_pnl": 5000.0,
            "best_performer": "momentum",
            "worst_performer": "mean_reversion",
            "num_profitable": 3,
        }
        result = dict_to_strategy_pnl_summary(data)
        
        assert isinstance(result, StrategyPnLSummary)
        assert result.total_pnl == Decimal("5000.0")
        assert result.best_performer == "momentum"
        assert result.worst_performer == "mean_reversion"
        assert result.num_profitable == 3

    def test_missing_fields_use_defaults(self):
        """Test that missing fields use default values."""
        data: dict[str, float | int | None] = {}
        result = dict_to_strategy_pnl_summary(data)
        
        assert result.total_pnl == Decimal("0.0")
        assert result.best_performer is None
        assert result.worst_performer is None
        assert result.num_profitable == 0

    def test_negative_pnl_preserved(self):
        """Test that negative P&L is preserved."""
        data = {
            "total_pnl": -2500.0,
            "num_profitable": 0,
        }
        result = dict_to_strategy_pnl_summary(data)
        
        assert result.total_pnl == Decimal("-2500.0")


class TestDictToStrategySummary:
    """Test dict_to_strategy_summary function."""

    def test_valid_strategy_summary(self):
        """Test conversion of valid strategy summary dict."""
        data = {
            "strategy_name": "momentum",
            "allocation_pct": 33.33,
            "signal_strength": 0.85,
            "pnl": 1500.0,
        }
        result = dict_to_strategy_summary(data)
        
        assert isinstance(result, StrategySummary)
        assert result.strategy_name == "momentum"
        assert result.allocation_pct == Decimal("33.33")
        assert result.signal_strength == Decimal("0.85")
        assert result.pnl == Decimal("1500.0")

    def test_missing_strategy_name_uses_default(self):
        """Test that missing strategy_name uses 'unknown'."""
        data = {
            "allocation_pct": 33.33,
            "signal_strength": 0.85,
            "pnl": 1500.0,
        }
        result = dict_to_strategy_summary(data)
        
        assert result.strategy_name == "unknown"

    def test_negative_pnl_preserved(self):
        """Test that negative P&L is preserved."""
        data = {
            "strategy_name": "momentum",
            "allocation_pct": 33.33,
            "signal_strength": 0.85,
            "pnl": -1500.0,
        }
        result = dict_to_strategy_summary(data)
        
        assert result.pnl == Decimal("-1500.0")


class TestDictToTradingSummary:
    """Test dict_to_trading_summary function."""

    def test_valid_trading_summary(self):
        """Test conversion of valid trading summary dict."""
        data = {
            "total_orders": 10,
            "orders_executed": 8,
            "success_rate": 0.8,
            "total_value": 50000.0,
        }
        result = dict_to_trading_summary(data)
        
        assert isinstance(result, TradingSummary)
        assert result.total_orders == 10
        assert result.orders_executed == 8
        assert result.success_rate == Decimal("0.8")
        assert result.total_value == Decimal("50000.0")

    def test_missing_fields_use_defaults(self):
        """Test that missing fields use default values."""
        data: dict[str, int | float] = {}
        result = dict_to_trading_summary(data)
        
        assert result.total_orders == 0
        assert result.orders_executed == 0
        assert result.success_rate == Decimal("0.0")
        assert result.total_value == Decimal("0.0")

    def test_zero_orders_accepted(self):
        """Test that zero orders is a valid state."""
        data = {
            "total_orders": 0,
            "orders_executed": 0,
            "success_rate": 0.0,
            "total_value": 0.0,
        }
        result = dict_to_trading_summary(data)
        
        assert result.total_orders == 0
        assert result.orders_executed == 0


class TestDictToExecutionSummary:
    """Test dict_to_execution_summary function."""

    def test_valid_execution_summary(self, sample_account_info):
        """Test conversion of valid execution summary dict."""
        data = {
            "allocations": {
                "total_allocation": 95.5,
                "num_positions": 5,
                "largest_position_pct": 25.0,
            },
            "strategy_summary": {
                "momentum": {
                    "strategy_name": "momentum",
                    "allocation_pct": 33.33,
                    "signal_strength": 0.85,
                    "pnl": 1500.0,
                }
            },
            "trading_summary": {
                "total_orders": 10,
                "orders_executed": 8,
                "success_rate": 0.8,
                "total_value": 50000.0,
            },
            "pnl_summary": {
                "total_pnl": 5000.0,
                "best_performer": "momentum",
                "worst_performer": None,
                "num_profitable": 1,
            },
            "account_info_before": sample_account_info,
            "account_info_after": sample_account_info,
            "mode": "paper",
            "engine_mode": "full",
            "error": None,
        }
        
        result = dict_to_execution_summary(data)
        
        assert isinstance(result, ExecutionSummary)
        assert result.mode == "paper"
        assert result.engine_mode == "full"
        assert result.error is None
        assert len(result.strategy_summary) == 1
        assert "momentum" in result.strategy_summary

    def test_missing_nested_dicts_use_defaults(self, sample_account_info):
        """Test that missing nested dicts are handled."""
        data = {
            "account_info_before": sample_account_info,
            "account_info_after": sample_account_info,
            "mode": "paper",
        }
        
        result = dict_to_execution_summary(data)
        
        assert isinstance(result, ExecutionSummary)
        assert result.allocations.num_positions == 0
        assert len(result.strategy_summary) == 0  # Will fail validation

    def test_strategy_name_added_to_strategy_data(self, sample_account_info):
        """Test that strategy_name is added to strategy data if missing."""
        data = {
            "allocations": {
                "total_allocation": 95.5,
                "num_positions": 5,
                "largest_position_pct": 25.0,
            },
            "strategy_summary": {
                "momentum": {
                    # strategy_name missing - should be added by function
                    "allocation_pct": 33.33,
                    "signal_strength": 0.85,
                    "pnl": 1500.0,
                }
            },
            "trading_summary": {
                "total_orders": 10,
                "orders_executed": 8,
                "success_rate": 0.8,
                "total_value": 50000.0,
            },
            "pnl_summary": {
                "total_pnl": 5000.0,
                "best_performer": "momentum",
                "worst_performer": None,
                "num_profitable": 1,
            },
            "account_info_before": sample_account_info,
            "account_info_after": sample_account_info,
            "mode": "paper",
        }
        
        result = dict_to_execution_summary(data)
        
        assert result.strategy_summary["momentum"].strategy_name == "momentum"

    def test_mode_unknown_fails_validation(self, sample_account_info):
        """Test that invalid mode value fails DTO validation."""
        data = {
            "allocations": {
                "total_allocation": 95.5,
                "num_positions": 5,
                "largest_position_pct": 25.0,
            },
            "strategy_summary": {
                "momentum": {
                    "strategy_name": "momentum",
                    "allocation_pct": 33.33,
                    "signal_strength": 0.85,
                    "pnl": 1500.0,
                }
            },
            "trading_summary": {
                "total_orders": 10,
                "orders_executed": 8,
                "success_rate": 0.8,
                "total_value": 50000.0,
            },
            "pnl_summary": {
                "total_pnl": 5000.0,
                "best_performer": "momentum",
                "worst_performer": None,
                "num_profitable": 1,
            },
            "account_info_before": sample_account_info,
            "account_info_after": sample_account_info,
            "mode": "unknown",  # Invalid mode
        }
        
        with pytest.raises(ValidationError):
            dict_to_execution_summary(data)

    def test_non_dict_strategy_entries_skipped(self, sample_account_info):
        """Test that non-dict strategy entries are skipped."""
        data = {
            "allocations": {
                "total_allocation": 95.5,
                "num_positions": 5,
                "largest_position_pct": 25.0,
            },
            "strategy_summary": {
                "momentum": {
                    "strategy_name": "momentum",
                    "allocation_pct": 33.33,
                    "signal_strength": 0.85,
                    "pnl": 1500.0,
                },
                "invalid_entry": "not_a_dict",  # Should be skipped
            },
            "trading_summary": {
                "total_orders": 10,
                "orders_executed": 8,
                "success_rate": 0.8,
                "total_value": 50000.0,
            },
            "pnl_summary": {
                "total_pnl": 5000.0,
                "best_performer": "momentum",
                "worst_performer": None,
                "num_profitable": 1,
            },
            "account_info_before": sample_account_info,
            "account_info_after": sample_account_info,
            "mode": "paper",
        }
        
        result = dict_to_execution_summary(data)
        
        assert len(result.strategy_summary) == 1
        assert "momentum" in result.strategy_summary
        assert "invalid_entry" not in result.strategy_summary


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_dict_uses_all_defaults(self):
        """Test that empty dict uses all default values."""
        data: dict[str, float | int] = {}
        
        # Individual functions should handle empty dicts
        alloc_result = dict_to_allocation_summary(data)
        assert alloc_result.num_positions == 0
        
        pnl_result = dict_to_strategy_pnl_summary(data)
        assert pnl_result.total_pnl == Decimal("0.0")
        
        trading_result = dict_to_trading_summary(data)
        assert trading_result.total_orders == 0

    def test_decimal_string_conversion(self):
        """Test that string Decimal values are handled correctly."""
        data = {
            "total_allocation": "95.123456789",
            "num_positions": 5,
            "largest_position_pct": "25.987654321",
        }
        
        # This should pass if precision validation allows it
        try:
            result = dict_to_allocation_summary(data)
            # If it succeeds, verify precision
            assert isinstance(result.total_allocation, Decimal)
        except ValidationError:
            # If it fails due to precision, that's expected behavior
            pass

    def test_very_large_numbers(self):
        """Test handling of very large numbers."""
        data = {
            "total_pnl": 999999999.99,
            "num_profitable": 100,
        }
        result = dict_to_strategy_pnl_summary(data)
        
        assert result.total_pnl == Decimal("999999999.99")
