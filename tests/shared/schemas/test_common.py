"""Business Unit: shared | Status: current

Unit tests for common DTOs.

Tests DTO validation, constraints, immutability, and serialization for
MultiStrategyExecutionResult, AllocationComparison, MultiStrategySummary,
Configuration, and Error DTOs.
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.common import (
    AllocationComparison,
    Configuration,
    Error,
    MultiStrategyExecutionResult,
    MultiStrategySummary,
)
from the_alchemiser.shared.schemas.execution_summary import (
    AllocationSummary,
    ExecutionSummary,
    StrategyPnLSummary,
    StrategySummary,
    TradingSummary,
)
from the_alchemiser.shared.schemas.portfolio_state import PortfolioState
from the_alchemiser.shared.value_objects.core_types import (
    AccountInfo,
    OrderDetails,
    StrategySignal,
)


class TestAllocationComparison:
    """Test AllocationComparison DTO validation."""

    def test_valid_allocation_comparison(self):
        """Test creation of valid allocation comparison."""
        comparison = AllocationComparison(
            target_values={"SPY": Decimal("50.0"), "QQQ": Decimal("50.0")},
            current_values={"SPY": Decimal("45.0"), "QQQ": Decimal("55.0")},
            deltas={"SPY": Decimal("5.0"), "QQQ": Decimal("-5.0")},
        )
        assert comparison.target_values["SPY"] == Decimal("50.0")
        assert comparison.current_values["SPY"] == Decimal("45.0")
        assert comparison.deltas["SPY"] == Decimal("5.0")

    def test_immutability(self):
        """Test that DTO is frozen."""
        comparison = AllocationComparison(
            target_values={"SPY": Decimal("50.0")},
            current_values={"SPY": Decimal("45.0")},
            deltas={"SPY": Decimal("5.0")},
        )
        with pytest.raises(ValidationError):
            comparison.target_values = {}  # type: ignore

    def test_decimal_precision_maintained(self):
        """Test that Decimal precision is maintained."""
        comparison = AllocationComparison(
            target_values={"SPY": Decimal("33.333333")},
            current_values={"SPY": Decimal("33.333334")},
            deltas={"SPY": Decimal("0.000001")},
        )
        assert comparison.target_values["SPY"] == Decimal("33.333333")
        assert comparison.deltas["SPY"] == Decimal("0.000001")

    def test_empty_dicts_allowed(self):
        """Test that empty dicts are allowed."""
        comparison = AllocationComparison(
            target_values={},
            current_values={},
            deltas={},
        )
        assert comparison.target_values == {}

    def test_serialization_round_trip(self):
        """Test that DTO can be serialized and deserialized."""
        original = AllocationComparison(
            target_values={"SPY": Decimal("50.0")},
            current_values={"SPY": Decimal("45.0")},
            deltas={"SPY": Decimal("5.0")},
        )
        dumped = original.model_dump()
        restored = AllocationComparison(**dumped)
        assert restored.target_values == original.target_values
        assert restored.current_values == original.current_values
        assert restored.deltas == original.deltas


class TestMultiStrategyExecutionResult:
    """Test MultiStrategyExecutionResult DTO validation."""

    @pytest.fixture
    def valid_account_info(self) -> AccountInfo:
        """Create a valid AccountInfo for tests."""
        return {
            "account_id": "test123",
            "equity": Decimal("100000.00"),
            "cash": Decimal("50000.00"),
            "buying_power": Decimal("100000.00"),
            "day_trades_remaining": 3,
            "portfolio_value": Decimal("100000.00"),
            "last_equity": Decimal("99000.00"),
            "daytrading_buying_power": Decimal("100000.00"),
            "regt_buying_power": Decimal("100000.00"),
            "status": "ACTIVE",
        }

    @pytest.fixture
    def valid_strategy_signals(self) -> dict[str, StrategySignal]:
        """Create valid strategy signals for tests."""
        return {
            "nuclear": {
                "symbol": "SPY",
                "action": "BUY",
                "allocation_percentage": Decimal("0.5"),
            }
        }

    @pytest.fixture
    def valid_execution_summary(self, valid_account_info: AccountInfo) -> ExecutionSummary:
        """Create a valid ExecutionSummary for tests."""
        return ExecutionSummary(
            allocations=AllocationSummary(
                total_allocation=Decimal("100.0"),
                num_positions=1,
                largest_position_pct=Decimal("100.0"),
            ),
            strategy_summary={},
            trading_summary=TradingSummary(
                total_orders=1,
                orders_executed=1,
                success_rate=Decimal("1.0"),
                total_value=Decimal("1000.00"),
            ),
            pnl_summary=StrategyPnLSummary(
                total_pnl=Decimal("0.00"),
                num_profitable=0,
            ),
            account_info_before=valid_account_info,
            account_info_after=valid_account_info,
            mode="paper",
        )

    def test_valid_execution_result(
        self,
        valid_account_info: AccountInfo,
        valid_strategy_signals: dict[str, StrategySignal],
        valid_execution_summary: ExecutionSummary,
    ):
        """Test creation of valid execution result."""
        result = MultiStrategyExecutionResult(
            success=True,
            strategy_signals=valid_strategy_signals,
            consolidated_portfolio={"SPY": Decimal("100.0")},
            orders_executed=[],
            account_info_before=valid_account_info,
            account_info_after=valid_account_info,
            execution_summary=valid_execution_summary,
        )
        assert result.success is True
        assert "nuclear" in result.strategy_signals
        assert result.consolidated_portfolio["SPY"] == Decimal("100.0")

    def test_immutability(
        self,
        valid_account_info: AccountInfo,
        valid_strategy_signals: dict[str, StrategySignal],
        valid_execution_summary: ExecutionSummary,
    ):
        """Test that DTO is frozen."""
        result = MultiStrategyExecutionResult(
            success=True,
            strategy_signals=valid_strategy_signals,
            consolidated_portfolio={},
            orders_executed=[],
            account_info_before=valid_account_info,
            account_info_after=valid_account_info,
            execution_summary=valid_execution_summary,
        )
        with pytest.raises(ValidationError):
            result.success = False  # type: ignore

    def test_optional_portfolio_state(
        self,
        valid_account_info: AccountInfo,
        valid_strategy_signals: dict[str, StrategySignal],
        valid_execution_summary: ExecutionSummary,
    ):
        """Test that portfolio_state is optional."""
        result = MultiStrategyExecutionResult(
            success=True,
            strategy_signals=valid_strategy_signals,
            consolidated_portfolio={},
            orders_executed=[],
            account_info_before=valid_account_info,
            account_info_after=valid_account_info,
            execution_summary=valid_execution_summary,
            final_portfolio_state=None,
        )
        assert result.final_portfolio_state is None


class TestMultiStrategySummary:
    """Test MultiStrategySummary DTO validation."""

    @pytest.fixture
    def valid_execution_result(self) -> MultiStrategyExecutionResult:
        """Create a valid MultiStrategyExecutionResult for tests."""
        account_info: AccountInfo = {
            "account_id": "test123",
            "equity": Decimal("100000.00"),
            "cash": Decimal("50000.00"),
            "buying_power": Decimal("100000.00"),
            "day_trades_remaining": 3,
            "portfolio_value": Decimal("100000.00"),
            "last_equity": Decimal("99000.00"),
            "daytrading_buying_power": Decimal("100000.00"),
            "regt_buying_power": Decimal("100000.00"),
            "status": "ACTIVE",
        }
        execution_summary = ExecutionSummary(
            allocations=AllocationSummary(
                total_allocation=Decimal("100.0"),
                num_positions=1,
                largest_position_pct=Decimal("100.0"),
            ),
            strategy_summary={},
            trading_summary=TradingSummary(
                total_orders=1,
                orders_executed=1,
                success_rate=Decimal("1.0"),
                total_value=Decimal("1000.00"),
            ),
            pnl_summary=StrategyPnLSummary(
                total_pnl=Decimal("0.00"),
                num_profitable=0,
            ),
            account_info_before=account_info,
            account_info_after=account_info,
            mode="paper",
        )
        return MultiStrategyExecutionResult(
            success=True,
            strategy_signals={},
            consolidated_portfolio={},
            orders_executed=[],
            account_info_before=account_info,
            account_info_after=account_info,
            execution_summary=execution_summary,
        )

    def test_valid_summary(self, valid_execution_result: MultiStrategyExecutionResult):
        """Test creation of valid summary."""
        summary = MultiStrategySummary(
            execution_result=valid_execution_result,
        )
        assert summary.execution_result.success is True
        assert summary.allocation_comparison is None
        assert summary.enriched_account is None
        assert summary.closed_pnl_subset is None

    def test_with_allocation_comparison(
        self, valid_execution_result: MultiStrategyExecutionResult
    ):
        """Test summary with allocation comparison."""
        comparison = AllocationComparison(
            target_values={"SPY": Decimal("50.0")},
            current_values={"SPY": Decimal("45.0")},
            deltas={"SPY": Decimal("5.0")},
        )
        summary = MultiStrategySummary(
            execution_result=valid_execution_result,
            allocation_comparison=comparison,
        )
        assert summary.allocation_comparison is not None
        assert summary.allocation_comparison.target_values["SPY"] == Decimal("50.0")

    def test_with_enriched_account(
        self, valid_execution_result: MultiStrategyExecutionResult
    ):
        """Test summary with enriched account data."""
        summary = MultiStrategySummary(
            execution_result=valid_execution_result,
            enriched_account={"equity": 100000.0, "cash": 50000.0},
        )
        assert summary.enriched_account is not None
        assert summary.enriched_account["equity"] == 100000.0

    def test_immutability(self, valid_execution_result: MultiStrategyExecutionResult):
        """Test that DTO is frozen."""
        summary = MultiStrategySummary(
            execution_result=valid_execution_result,
        )
        with pytest.raises(ValidationError):
            summary.allocation_comparison = None  # type: ignore


class TestConfiguration:
    """Test Configuration DTO validation."""

    def test_default_config(self):
        """Test creation with default config_data."""
        config = Configuration()
        assert config.config_data == {}

    def test_with_config_data(self):
        """Test creation with config_data."""
        config = Configuration(
            config_data={"stage": "paper", "region": "us-east-1"}
        )
        assert config.config_data["stage"] == "paper"
        assert config.config_data["region"] == "us-east-1"

    def test_immutability(self):
        """Test that DTO is frozen."""
        config = Configuration()
        with pytest.raises(ValidationError):
            config.config_data = {}  # type: ignore

    def test_serialization_round_trip(self):
        """Test that DTO can be serialized and deserialized."""
        original = Configuration(config_data={"key": "value"})
        dumped = original.model_dump()
        restored = Configuration(**dumped)
        assert restored.config_data == original.config_data


class TestError:
    """Test Error DTO validation."""

    def test_minimal_error(self):
        """Test creation with minimal required fields."""
        error = Error(
            error_type="ValidationError",
            message="Invalid input",
        )
        assert error.error_type == "ValidationError"
        assert error.message == "Invalid input"
        assert error.context == {}

    def test_with_context(self):
        """Test creation with context."""
        error = Error(
            error_type="APIError",
            message="API call failed",
            context={"status_code": 500, "endpoint": "/api/orders"},
        )
        assert error.context["status_code"] == 500
        assert error.context["endpoint"] == "/api/orders"

    def test_immutability(self):
        """Test that DTO is frozen."""
        error = Error(
            error_type="TestError",
            message="Test",
        )
        with pytest.raises(ValidationError):
            error.message = "Modified"  # type: ignore

    def test_serialization_round_trip(self):
        """Test that DTO can be serialized and deserialized."""
        original = Error(
            error_type="TestError",
            message="Test message",
            context={"key": "value"},
        )
        dumped = original.model_dump()
        restored = Error(**dumped)
        assert restored.error_type == original.error_type
        assert restored.message == original.message
        assert restored.context == original.context

    def test_string_fields_validation(self):
        """Test string field validation."""
        # Pydantic with strict mode accepts empty strings by default
        # This test validates that the fields accept string types
        error = Error(error_type="", message="")
        assert error.error_type == ""
        assert error.message == ""
