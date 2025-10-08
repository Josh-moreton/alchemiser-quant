"""Business Unit: shared | Status: current

Comprehensive unit tests for execution summary DTOs.

Tests DTO validation, constraints, immutability, field validators,
model validators, and edge cases for all execution summary schemas.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.execution_summary import (
    AllocationSummary,
    EngineMode,
    ExecutionMode,
    ExecutionSummary,
    PortfolioState,
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


class TestAllocationSummary:
    """Test AllocationSummary DTO validation."""

    def test_valid_allocation_summary(self):
        """Test creation of valid allocation summary."""
        summary = AllocationSummary(
            total_allocation=Decimal("95.50"),
            num_positions=5,
            largest_position_pct=Decimal("25.00"),
        )
        assert summary.total_allocation == Decimal("95.50")
        assert summary.num_positions == 5
        assert summary.largest_position_pct == Decimal("25.00")
        assert summary.schema_version == "1.0"

    def test_immutability(self):
        """Test that DTO is frozen."""
        summary = AllocationSummary(
            total_allocation=Decimal("95.50"),
            num_positions=5,
            largest_position_pct=Decimal("25.00"),
        )
        with pytest.raises(ValidationError):
            summary.num_positions = 10  # type: ignore[misc]

    def test_total_allocation_exceeds_100_rejected(self):
        """Test total_allocation > 100 is rejected."""
        with pytest.raises(ValidationError):
            AllocationSummary(
                total_allocation=Decimal("100.01"),
                num_positions=5,
                largest_position_pct=Decimal("25.00"),
            )

    def test_negative_num_positions_rejected(self):
        """Test negative num_positions is rejected."""
        with pytest.raises(ValidationError):
            AllocationSummary(
                total_allocation=Decimal("95.50"),
                num_positions=-1,
                largest_position_pct=Decimal("25.00"),
            )

    def test_largest_position_exceeds_100_rejected(self):
        """Test largest_position_pct > 100 is rejected."""
        with pytest.raises(ValidationError):
            AllocationSummary(
                total_allocation=Decimal("95.50"),
                num_positions=5,
                largest_position_pct=Decimal("100.01"),
            )

    def test_precision_validation_percentage(self):
        """Test precision validation for percentage fields."""
        # Valid: 4 decimal places
        summary = AllocationSummary(
            total_allocation=Decimal("95.1234"),
            num_positions=5,
            largest_position_pct=Decimal("25.5678"),
        )
        assert summary.total_allocation == Decimal("95.1234")

        # Invalid: 5 decimal places
        with pytest.raises(ValidationError, match="precision too high"):
            AllocationSummary(
                total_allocation=Decimal("95.12345"),
                num_positions=5,
                largest_position_pct=Decimal("25.00"),
            )

    def test_zero_values_accepted(self):
        """Test that zero values are valid."""
        summary = AllocationSummary(
            total_allocation=Decimal("0"),
            num_positions=0,
            largest_position_pct=Decimal("0"),
        )
        assert summary.num_positions == 0


class TestStrategyPnLSummary:
    """Test StrategyPnLSummary DTO validation."""

    def test_valid_pnl_summary(self):
        """Test creation of valid P&L summary."""
        summary = StrategyPnLSummary(
            total_pnl=Decimal("5000.00"),
            best_performer="momentum",
            worst_performer="mean_reversion",
            num_profitable=3,
        )
        assert summary.total_pnl == Decimal("5000.00")
        assert summary.best_performer == "momentum"
        assert summary.worst_performer == "mean_reversion"
        assert summary.num_profitable == 3
        assert summary.schema_version == "1.0"

    def test_negative_pnl_accepted(self):
        """Test that negative P&L is valid."""
        summary = StrategyPnLSummary(
            total_pnl=Decimal("-2500.00"),
            best_performer=None,
            worst_performer=None,
            num_profitable=0,
        )
        assert summary.total_pnl == Decimal("-2500.00")

    def test_optional_performers_none(self):
        """Test that performer fields can be None."""
        summary = StrategyPnLSummary(
            total_pnl=Decimal("0"),
            best_performer=None,
            worst_performer=None,
            num_profitable=0,
        )
        assert summary.best_performer is None
        assert summary.worst_performer is None

    def test_empty_string_performer_rejected(self):
        """Test that empty string performers are rejected."""
        with pytest.raises(ValidationError):
            StrategyPnLSummary(
                total_pnl=Decimal("0"),
                best_performer="",
                worst_performer=None,
                num_profitable=0,
            )

    def test_long_performer_name_rejected(self):
        """Test that excessively long performer names are rejected."""
        with pytest.raises(ValidationError):
            StrategyPnLSummary(
                total_pnl=Decimal("0"),
                best_performer="x" * 101,  # 101 chars
                worst_performer=None,
                num_profitable=0,
            )


class TestStrategySummary:
    """Test StrategySummary DTO validation."""

    def test_valid_strategy_summary(self):
        """Test creation of valid strategy summary."""
        summary = StrategySummary(
            strategy_name="momentum",
            allocation_pct=Decimal("33.33"),
            signal_strength=Decimal("0.85"),
            pnl=Decimal("1500.00"),
        )
        assert summary.strategy_name == "momentum"
        assert summary.allocation_pct == Decimal("33.33")
        assert summary.signal_strength == Decimal("0.85")
        assert summary.pnl == Decimal("1500.00")
        assert summary.schema_version == "1.0"

    def test_allocation_pct_exceeds_100_rejected(self):
        """Test allocation_pct > 100 is rejected."""
        with pytest.raises(ValidationError):
            StrategySummary(
                strategy_name="momentum",
                allocation_pct=Decimal("100.01"),
                signal_strength=Decimal("0.85"),
                pnl=Decimal("1500.00"),
            )

    def test_signal_strength_exceeds_1_rejected(self):
        """Test signal_strength > 1 is rejected."""
        with pytest.raises(ValidationError):
            StrategySummary(
                strategy_name="momentum",
                allocation_pct=Decimal("33.33"),
                signal_strength=Decimal("1.01"),
                pnl=Decimal("1500.00"),
            )

    def test_negative_signal_strength_rejected(self):
        """Test negative signal_strength is rejected."""
        with pytest.raises(ValidationError):
            StrategySummary(
                strategy_name="momentum",
                allocation_pct=Decimal("33.33"),
                signal_strength=Decimal("-0.1"),
                pnl=Decimal("1500.00"),
            )

    def test_negative_pnl_accepted(self):
        """Test that negative P&L is valid."""
        summary = StrategySummary(
            strategy_name="momentum",
            allocation_pct=Decimal("33.33"),
            signal_strength=Decimal("0.85"),
            pnl=Decimal("-1500.00"),
        )
        assert summary.pnl == Decimal("-1500.00")

    def test_empty_strategy_name_rejected(self):
        """Test that empty strategy name is rejected."""
        with pytest.raises(ValidationError):
            StrategySummary(
                strategy_name="",
                allocation_pct=Decimal("33.33"),
                signal_strength=Decimal("0.85"),
                pnl=Decimal("1500.00"),
            )

    def test_allocation_precision_validation(self):
        """Test allocation percentage precision validation."""
        # Valid: 4 decimal places
        summary = StrategySummary(
            strategy_name="momentum",
            allocation_pct=Decimal("33.3333"),
            signal_strength=Decimal("0.85"),
            pnl=Decimal("1500.00"),
        )
        assert summary.allocation_pct == Decimal("33.3333")

        # Invalid: 5 decimal places
        with pytest.raises(ValidationError, match="precision too high"):
            StrategySummary(
                strategy_name="momentum",
                allocation_pct=Decimal("33.33333"),
                signal_strength=Decimal("0.85"),
                pnl=Decimal("1500.00"),
            )

    def test_signal_strength_precision_validation(self):
        """Test signal strength precision validation."""
        # Valid: 6 decimal places
        summary = StrategySummary(
            strategy_name="momentum",
            allocation_pct=Decimal("33.33"),
            signal_strength=Decimal("0.123456"),
            pnl=Decimal("1500.00"),
        )
        assert summary.signal_strength == Decimal("0.123456")

        # Invalid: 7 decimal places
        with pytest.raises(ValidationError, match="precision too high"):
            StrategySummary(
                strategy_name="momentum",
                allocation_pct=Decimal("33.33"),
                signal_strength=Decimal("0.1234567"),
                pnl=Decimal("1500.00"),
            )


class TestTradingSummary:
    """Test TradingSummary DTO validation."""

    def test_valid_trading_summary(self):
        """Test creation of valid trading summary."""
        summary = TradingSummary(
            total_orders=10,
            orders_executed=8,
            success_rate=Decimal("0.8"),
            total_value=Decimal("50000.00"),
        )
        assert summary.total_orders == 10
        assert summary.orders_executed == 8
        assert summary.success_rate == Decimal("0.8")
        assert summary.total_value == Decimal("50000.00")
        assert summary.schema_version == "1.0"

    def test_success_rate_exceeds_1_rejected(self):
        """Test success_rate > 1 is rejected."""
        with pytest.raises(ValidationError):
            TradingSummary(
                total_orders=10,
                orders_executed=8,
                success_rate=Decimal("1.01"),
                total_value=Decimal("50000.00"),
            )

    def test_negative_success_rate_rejected(self):
        """Test negative success_rate is rejected."""
        with pytest.raises(ValidationError):
            TradingSummary(
                total_orders=10,
                orders_executed=8,
                success_rate=Decimal("-0.1"),
                total_value=Decimal("50000.00"),
            )

    def test_negative_total_value_rejected(self):
        """Test negative total_value is rejected."""
        with pytest.raises(ValidationError):
            TradingSummary(
                total_orders=10,
                orders_executed=8,
                success_rate=Decimal("0.8"),
                total_value=Decimal("-1"),
            )

    def test_zero_orders_accepted(self):
        """Test that zero orders is valid."""
        summary = TradingSummary(
            total_orders=0,
            orders_executed=0,
            success_rate=Decimal("0"),
            total_value=Decimal("0"),
        )
        assert summary.total_orders == 0

    def test_success_rate_precision_validation(self):
        """Test success rate precision validation."""
        # Valid: 6 decimal places
        summary = TradingSummary(
            total_orders=10,
            orders_executed=8,
            success_rate=Decimal("0.123456"),
            total_value=Decimal("50000.00"),
        )
        assert summary.success_rate == Decimal("0.123456")

        # Invalid: 7 decimal places
        with pytest.raises(ValidationError, match="precision too high"):
            TradingSummary(
                total_orders=10,
                orders_executed=8,
                success_rate=Decimal("0.1234567"),
                total_value=Decimal("50000.00"),
            )


class TestExecutionSummary:
    """Test ExecutionSummary DTO validation."""

    def test_valid_execution_summary(self, sample_account_info):
        """Test creation of valid execution summary."""
        allocations = AllocationSummary(
            total_allocation=Decimal("95.50"),
            num_positions=5,
            largest_position_pct=Decimal("25.00"),
        )
        strategy_summary = {
            "momentum": StrategySummary(
                strategy_name="momentum",
                allocation_pct=Decimal("33.33"),
                signal_strength=Decimal("0.85"),
                pnl=Decimal("1500.00"),
            )
        }
        trading_summary = TradingSummary(
            total_orders=10,
            orders_executed=8,
            success_rate=Decimal("0.8"),
            total_value=Decimal("50000.00"),
        )
        pnl_summary = StrategyPnLSummary(
            total_pnl=Decimal("5000.00"),
            best_performer="momentum",
            worst_performer=None,
            num_profitable=1,
        )

        summary = ExecutionSummary(
            allocations=allocations,
            strategy_summary=strategy_summary,
            trading_summary=trading_summary,
            pnl_summary=pnl_summary,
            account_info_before=sample_account_info,
            account_info_after=sample_account_info,
            mode="paper",
            engine_mode="full",
            error=None,
        )

        assert summary.mode == "paper"
        assert summary.engine_mode == "full"
        assert summary.error is None
        assert summary.schema_version == "1.0"

    def test_mode_literal_enforcement(self, sample_account_info):
        """Test that mode field only accepts 'paper' or 'live'."""
        allocations = AllocationSummary(
            total_allocation=Decimal("95.50"),
            num_positions=5,
            largest_position_pct=Decimal("25.00"),
        )
        strategy_summary = {
            "momentum": StrategySummary(
                strategy_name="momentum",
                allocation_pct=Decimal("33.33"),
                signal_strength=Decimal("0.85"),
                pnl=Decimal("1500.00"),
            )
        }
        trading_summary = TradingSummary(
            total_orders=10,
            orders_executed=8,
            success_rate=Decimal("0.8"),
            total_value=Decimal("50000.00"),
        )
        pnl_summary = StrategyPnLSummary(
            total_pnl=Decimal("5000.00"),
            best_performer="momentum",
            worst_performer=None,
            num_profitable=1,
        )

        # Valid modes
        for mode in ["paper", "live"]:
            summary = ExecutionSummary(
                allocations=allocations,
                strategy_summary=strategy_summary,
                trading_summary=trading_summary,
                pnl_summary=pnl_summary,
                account_info_before=sample_account_info,
                account_info_after=sample_account_info,
                mode=mode,  # type: ignore[arg-type]
            )
            assert summary.mode == mode

        # Invalid mode
        with pytest.raises(ValidationError):
            ExecutionSummary(
                allocations=allocations,
                strategy_summary=strategy_summary,
                trading_summary=trading_summary,
                pnl_summary=pnl_summary,
                account_info_before=sample_account_info,
                account_info_after=sample_account_info,
                mode="test",  # type: ignore[arg-type]
            )

    def test_engine_mode_literal_enforcement(self, sample_account_info):
        """Test that engine_mode field only accepts valid values."""
        allocations = AllocationSummary(
            total_allocation=Decimal("95.50"),
            num_positions=5,
            largest_position_pct=Decimal("25.00"),
        )
        strategy_summary = {
            "momentum": StrategySummary(
                strategy_name="momentum",
                allocation_pct=Decimal("33.33"),
                signal_strength=Decimal("0.85"),
                pnl=Decimal("1500.00"),
            )
        }
        trading_summary = TradingSummary(
            total_orders=10,
            orders_executed=8,
            success_rate=Decimal("0.8"),
            total_value=Decimal("50000.00"),
        )
        pnl_summary = StrategyPnLSummary(
            total_pnl=Decimal("5000.00"),
            best_performer="momentum",
            worst_performer=None,
            num_profitable=1,
        )

        # Valid engine modes
        for engine_mode in ["full", "signal_only", "execution_only", None]:
            summary = ExecutionSummary(
                allocations=allocations,
                strategy_summary=strategy_summary,
                trading_summary=trading_summary,
                pnl_summary=pnl_summary,
                account_info_before=sample_account_info,
                account_info_after=sample_account_info,
                mode="paper",
                engine_mode=engine_mode,  # type: ignore[arg-type]
            )
            assert summary.engine_mode == engine_mode

        # Invalid engine mode
        with pytest.raises(ValidationError):
            ExecutionSummary(
                allocations=allocations,
                strategy_summary=strategy_summary,
                trading_summary=trading_summary,
                pnl_summary=pnl_summary,
                account_info_before=sample_account_info,
                account_info_after=sample_account_info,
                mode="paper",
                engine_mode="invalid",  # type: ignore[arg-type]
            )

    def test_empty_strategy_summary_rejected(self, sample_account_info):
        """Test that empty strategy_summary dict is rejected."""
        allocations = AllocationSummary(
            total_allocation=Decimal("95.50"),
            num_positions=5,
            largest_position_pct=Decimal("25.00"),
        )
        trading_summary = TradingSummary(
            total_orders=10,
            orders_executed=8,
            success_rate=Decimal("0.8"),
            total_value=Decimal("50000.00"),
        )
        pnl_summary = StrategyPnLSummary(
            total_pnl=Decimal("5000.00"),
            best_performer="momentum",
            worst_performer=None,
            num_profitable=1,
        )

        with pytest.raises(ValidationError, match="cannot be empty"):
            ExecutionSummary(
                allocations=allocations,
                strategy_summary={},  # Empty dict
                trading_summary=trading_summary,
                pnl_summary=pnl_summary,
                account_info_before=sample_account_info,
                account_info_after=sample_account_info,
                mode="paper",
            )

    def test_strategy_summary_key_mismatch_rejected(self, sample_account_info):
        """Test that mismatched keys and strategy names are rejected."""
        allocations = AllocationSummary(
            total_allocation=Decimal("95.50"),
            num_positions=5,
            largest_position_pct=Decimal("25.00"),
        )
        strategy_summary = {
            "wrong_key": StrategySummary(
                strategy_name="momentum",  # Name doesn't match key
                allocation_pct=Decimal("33.33"),
                signal_strength=Decimal("0.85"),
                pnl=Decimal("1500.00"),
            )
        }
        trading_summary = TradingSummary(
            total_orders=10,
            orders_executed=8,
            success_rate=Decimal("0.8"),
            total_value=Decimal("50000.00"),
        )
        pnl_summary = StrategyPnLSummary(
            total_pnl=Decimal("5000.00"),
            best_performer="momentum",
            worst_performer=None,
            num_profitable=1,
        )

        with pytest.raises(ValidationError, match="does not match strategy_name"):
            ExecutionSummary(
                allocations=allocations,
                strategy_summary=strategy_summary,
                trading_summary=trading_summary,
                pnl_summary=pnl_summary,
                account_info_before=sample_account_info,
                account_info_after=sample_account_info,
                mode="paper",
            )

    def test_error_message_max_length(self, sample_account_info):
        """Test that error messages respect max length."""
        allocations = AllocationSummary(
            total_allocation=Decimal("95.50"),
            num_positions=5,
            largest_position_pct=Decimal("25.00"),
        )
        strategy_summary = {
            "momentum": StrategySummary(
                strategy_name="momentum",
                allocation_pct=Decimal("33.33"),
                signal_strength=Decimal("0.85"),
                pnl=Decimal("1500.00"),
            )
        }
        trading_summary = TradingSummary(
            total_orders=10,
            orders_executed=8,
            success_rate=Decimal("0.8"),
            total_value=Decimal("50000.00"),
        )
        pnl_summary = StrategyPnLSummary(
            total_pnl=Decimal("5000.00"),
            best_performer="momentum",
            worst_performer=None,
            num_profitable=1,
        )

        # Valid: 2000 chars
        summary = ExecutionSummary(
            allocations=allocations,
            strategy_summary=strategy_summary,
            trading_summary=trading_summary,
            pnl_summary=pnl_summary,
            account_info_before=sample_account_info,
            account_info_after=sample_account_info,
            mode="paper",
            error="x" * 2000,
        )
        assert len(summary.error) == 2000  # type: ignore[arg-type]

        # Invalid: 2001 chars
        with pytest.raises(ValidationError):
            ExecutionSummary(
                allocations=allocations,
                strategy_summary=strategy_summary,
                trading_summary=trading_summary,
                pnl_summary=pnl_summary,
                account_info_before=sample_account_info,
                account_info_after=sample_account_info,
                mode="paper",
                error="x" * 2001,
            )


class TestPortfolioState:
    """Test PortfolioState DTO validation."""

    def test_valid_portfolio_state(self):
        """Test creation of valid portfolio state."""
        state = PortfolioState(
            total_portfolio_value=Decimal("100000.00"),
            target_allocations={"AAPL": Decimal("50.0"), "MSFT": Decimal("50.0")},
            current_allocations={"AAPL": Decimal("48.0"), "MSFT": Decimal("52.0")},
            target_values={"AAPL": Decimal("50000.00"), "MSFT": Decimal("50000.00")},
            current_values={"AAPL": Decimal("48000.00"), "MSFT": Decimal("52000.00")},
            allocation_discrepancies={"AAPL": Decimal("-2.0"), "MSFT": Decimal("2.0")},
            largest_discrepancy=Decimal("2.0"),
            total_symbols=2,
            rebalance_needed=True,
        )
        assert state.total_portfolio_value == Decimal("100000.00")
        assert state.total_symbols == 2
        assert state.rebalance_needed is True
        assert state.schema_version == "1.0"

    def test_symbol_consistency_validation(self):
        """Test that all dicts must have consistent symbols."""
        # Valid: all dicts have same symbols
        state = PortfolioState(
            total_portfolio_value=Decimal("100000.00"),
            target_allocations={"AAPL": Decimal("100.0")},
            current_allocations={"AAPL": Decimal("100.0")},
            target_values={"AAPL": Decimal("100000.00")},
            current_values={"AAPL": Decimal("100000.00")},
            allocation_discrepancies={"AAPL": Decimal("0")},
            largest_discrepancy=Decimal("0"),
            total_symbols=1,
            rebalance_needed=False,
        )
        assert state.total_symbols == 1

        # Invalid: inconsistent symbols
        with pytest.raises(ValidationError, match="Symbol sets must be consistent"):
            PortfolioState(
                total_portfolio_value=Decimal("100000.00"),
                target_allocations={"AAPL": Decimal("100.0")},
                current_allocations={"MSFT": Decimal("100.0")},  # Different symbol
                target_values={"AAPL": Decimal("100000.00")},
                current_values={"AAPL": Decimal("100000.00")},
                allocation_discrepancies={"AAPL": Decimal("0")},
                largest_discrepancy=Decimal("0"),
                total_symbols=1,
                rebalance_needed=False,
            )

    def test_total_symbols_count_validation(self):
        """Test that total_symbols matches actual symbol count."""
        # Valid: count matches
        state = PortfolioState(
            total_portfolio_value=Decimal("100000.00"),
            target_allocations={"AAPL": Decimal("50.0"), "MSFT": Decimal("50.0")},
            current_allocations={"AAPL": Decimal("48.0"), "MSFT": Decimal("52.0")},
            target_values={"AAPL": Decimal("50000.00"), "MSFT": Decimal("50000.00")},
            current_values={"AAPL": Decimal("48000.00"), "MSFT": Decimal("52000.00")},
            allocation_discrepancies={"AAPL": Decimal("-2.0"), "MSFT": Decimal("2.0")},
            largest_discrepancy=Decimal("2.0"),
            total_symbols=2,
            rebalance_needed=True,
        )
        assert state.total_symbols == 2

        # Invalid: count mismatch
        with pytest.raises(ValidationError, match="does not match actual symbol count"):
            PortfolioState(
                total_portfolio_value=Decimal("100000.00"),
                target_allocations={"AAPL": Decimal("100.0")},
                current_allocations={"AAPL": Decimal("100.0")},
                target_values={"AAPL": Decimal("100000.00")},
                current_values={"AAPL": Decimal("100000.00")},
                allocation_discrepancies={"AAPL": Decimal("0")},
                largest_discrepancy=Decimal("0"),
                total_symbols=5,  # Wrong count
                rebalance_needed=False,
            )

    def test_allocation_percentage_range_validation(self):
        """Test that allocation percentages are in valid range."""
        # Valid: 0-100 range
        state = PortfolioState(
            total_portfolio_value=Decimal("100000.00"),
            target_allocations={"AAPL": Decimal("0"), "MSFT": Decimal("100.0")},
            current_allocations={"AAPL": Decimal("0"), "MSFT": Decimal("100.0")},
            target_values={"AAPL": Decimal("0"), "MSFT": Decimal("100000.00")},
            current_values={"AAPL": Decimal("0"), "MSFT": Decimal("100000.00")},
            allocation_discrepancies={"AAPL": Decimal("0"), "MSFT": Decimal("0")},
            largest_discrepancy=Decimal("0"),
            total_symbols=2,
            rebalance_needed=False,
        )
        assert state.target_allocations["AAPL"] == Decimal("0")

        # Invalid: > 100
        with pytest.raises(ValidationError, match="must be between 0 and 100"):
            PortfolioState(
                total_portfolio_value=Decimal("100000.00"),
                target_allocations={"AAPL": Decimal("100.01")},
                current_allocations={"AAPL": Decimal("100.0")},
                target_values={"AAPL": Decimal("100000.00")},
                current_values={"AAPL": Decimal("100000.00")},
                allocation_discrepancies={"AAPL": Decimal("0")},
                largest_discrepancy=Decimal("0"),
                total_symbols=1,
                rebalance_needed=False,
            )

    def test_negative_values_rejected(self):
        """Test that negative dollar values are rejected."""
        with pytest.raises(ValidationError, match="cannot be negative"):
            PortfolioState(
                total_portfolio_value=Decimal("100000.00"),
                target_allocations={"AAPL": Decimal("100.0")},
                current_allocations={"AAPL": Decimal("100.0")},
                target_values={"AAPL": Decimal("-1000.00")},  # Negative value
                current_values={"AAPL": Decimal("100000.00")},
                allocation_discrepancies={"AAPL": Decimal("0")},
                largest_discrepancy=Decimal("0"),
                total_symbols=1,
                rebalance_needed=False,
            )

    def test_negative_total_portfolio_value_rejected(self):
        """Test that negative total portfolio value is rejected."""
        with pytest.raises(ValidationError):
            PortfolioState(
                total_portfolio_value=Decimal("-100000.00"),
                target_allocations={"AAPL": Decimal("100.0")},
                current_allocations={"AAPL": Decimal("100.0")},
                target_values={"AAPL": Decimal("100000.00")},
                current_values={"AAPL": Decimal("100000.00")},
                allocation_discrepancies={"AAPL": Decimal("0")},
                largest_discrepancy=Decimal("0"),
                total_symbols=1,
                rebalance_needed=False,
            )


class TestTypeAliases:
    """Test type alias enforcement."""

    def test_execution_mode_type_alias(self):
        """Test ExecutionMode type alias."""
        # These should be valid values
        mode1: ExecutionMode = "paper"
        mode2: ExecutionMode = "live"
        assert mode1 == "paper"
        assert mode2 == "live"

    def test_engine_mode_type_alias(self):
        """Test EngineMode type alias."""
        # These should be valid values
        mode1: EngineMode = "full"
        mode2: EngineMode = "signal_only"
        mode3: EngineMode = "execution_only"
        assert mode1 == "full"
        assert mode2 == "signal_only"
        assert mode3 == "execution_only"


class TestBackwardCompatibilityAliases:
    """Test backward compatibility aliases."""

    def test_dto_aliases_exist(self):
        """Test that backward compatibility aliases are available."""
        from the_alchemiser.shared.schemas.execution_summary import (
            AllocationSummaryDTO,
            ExecutionSummaryDTO,
            PortfolioStateDTO,
            StrategyPnLSummaryDTO,
            StrategySummaryDTO,
            TradingSummaryDTO,
        )

        # Verify aliases point to correct classes
        assert AllocationSummaryDTO is AllocationSummary
        assert StrategyPnLSummaryDTO is StrategyPnLSummary
        assert StrategySummaryDTO is StrategySummary
        assert TradingSummaryDTO is TradingSummary
        assert ExecutionSummaryDTO is ExecutionSummary
        assert PortfolioStateDTO is PortfolioState
