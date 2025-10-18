#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Unit tests for CLI schema validation.

Tests cover:
- Schema validation (bounds, types, constraints)
- Immutability (frozen models)
- Schema versioning
- Decimal precision for financial values
- Default values and field requirements
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.cli import (
    CLIAccountDisplay,
    CLICommandResult,
    CLIOptions,
    CLIOrderDisplay,
    CLIPortfolioData,
    CLISignalData,
)


class TestCLIOptions:
    """Test CLI options schema validation."""

    def test_default_values(self) -> None:
        """Test that all boolean flags default to False."""
        options = CLIOptions()

        assert options.verbose is False
        assert options.quiet is False
        assert options.live is False
        assert options.force is False
        assert options.no_header is False

    def test_schema_version(self) -> None:
        """Test schema version is included and defaults to 1.0."""
        options = CLIOptions()
        assert options.schema_version == "1.0"

    def test_immutability(self) -> None:
        """Test that CLIOptions is frozen and immutable."""
        options = CLIOptions(verbose=True)

        with pytest.raises(ValidationError):
            options.verbose = False  # type: ignore[misc]

    def test_explicit_values(self) -> None:
        """Test setting explicit values."""
        options = CLIOptions(verbose=True, quiet=False, live=True, force=True, no_header=True)

        assert options.verbose is True
        assert options.quiet is False
        assert options.live is True
        assert options.force is True
        assert options.no_header is True


class TestCLICommandResult:
    """Test CLI command result schema validation."""

    def test_valid_result(self) -> None:
        """Test creating a valid command result."""
        result = CLICommandResult(
            success=True, message="Command executed successfully", exit_code=0
        )

        assert result.success is True
        assert result.message == "Command executed successfully"
        assert result.exit_code == 0

    def test_schema_version(self) -> None:
        """Test schema version is included and defaults to 1.0."""
        result = CLICommandResult(success=False, message="Error occurred", exit_code=1)
        assert result.schema_version == "1.0"

    def test_exit_code_validation_lower_bound(self) -> None:
        """Test exit code cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            CLICommandResult(success=False, message="Error", exit_code=-1)

        assert "greater than or equal to 0" in str(exc_info.value)

    def test_exit_code_validation_upper_bound(self) -> None:
        """Test exit code cannot exceed 255."""
        with pytest.raises(ValidationError) as exc_info:
            CLICommandResult(success=False, message="Error", exit_code=256)

        assert "less than or equal to 255" in str(exc_info.value)

    def test_exit_code_boundary_values(self) -> None:
        """Test exit code boundary values 0 and 255 are valid."""
        result_min = CLICommandResult(success=True, message="OK", exit_code=0)
        result_max = CLICommandResult(success=False, message="Error", exit_code=255)

        assert result_min.exit_code == 0
        assert result_max.exit_code == 255

    def test_immutability(self) -> None:
        """Test that CLICommandResult is frozen and immutable."""
        result = CLICommandResult(success=True, message="OK", exit_code=0)

        with pytest.raises(ValidationError):
            result.success = False  # type: ignore[misc]


class TestCLISignalData:
    """Test CLI signal data schema validation."""

    def test_empty_defaults(self) -> None:
        """Test that signals and indicators default to empty dicts."""
        signal_data = CLISignalData(strategy_type="test_strategy")

        assert signal_data.strategy_type == "test_strategy"
        assert signal_data.signals == {}
        assert signal_data.indicators == {}

    def test_schema_version(self) -> None:
        """Test schema version is included and defaults to 1.0."""
        signal_data = CLISignalData(strategy_type="test")
        assert signal_data.schema_version == "1.0"

    def test_with_signals_and_indicators(self) -> None:
        """Test creating signal data with signals and indicators."""
        signals = {
            "AAPL": {"symbol": "AAPL", "action": "BUY"},
            "GOOGL": {"symbol": "GOOGL", "action": "HOLD"},
        }
        indicators = {"AAPL": {"rsi": 45.5, "macd": 1.23}, "GOOGL": {"rsi": 65.0, "macd": -0.5}}

        signal_data = CLISignalData(
            strategy_type="momentum",
            signals=signals,  # type: ignore[arg-type]
            indicators=indicators,
        )

        assert signal_data.strategy_type == "momentum"
        assert len(signal_data.signals) == 2
        assert len(signal_data.indicators) == 2
        assert signal_data.indicators["AAPL"]["rsi"] == 45.5

    def test_immutability(self) -> None:
        """Test that CLISignalData is frozen and immutable."""
        signal_data = CLISignalData(strategy_type="test")

        with pytest.raises(ValidationError):
            signal_data.strategy_type = "modified"  # type: ignore[misc]


class TestCLIAccountDisplay:
    """Test CLI account display schema validation."""

    def test_valid_account_display(self) -> None:
        """Test creating valid account display data."""
        account_info = {
            "account_id": "test123",
            "equity": Decimal("10000.00"),
            "cash": Decimal("5000.00"),
            "buying_power": Decimal("8000.00"),
            "day_trades_remaining": 3,
            "portfolio_value": Decimal("10000.00"),
            "last_equity": Decimal("9500.00"),
            "daytrading_buying_power": Decimal("8000.00"),
            "regt_buying_power": Decimal("7000.00"),
            "status": "ACTIVE",
        }

        display = CLIAccountDisplay(
            account_info=account_info,  # type: ignore[arg-type]
            positions={},
            mode="paper",
        )

        assert display.mode == "paper"
        assert display.account_info["account_id"] == "test123"  # type: ignore[index]
        assert display.positions == {}

    def test_schema_version(self) -> None:
        """Test schema version is included and defaults to 1.0."""
        account_info = {
            "account_id": "test",
            "equity": Decimal("1000"),
            "cash": Decimal("500"),
            "buying_power": Decimal("800"),
            "day_trades_remaining": 3,
            "portfolio_value": Decimal("1000"),
            "last_equity": Decimal("950"),
            "daytrading_buying_power": Decimal("800"),
            "regt_buying_power": Decimal("700"),
            "status": "ACTIVE",
        }

        display = CLIAccountDisplay(
            account_info=account_info,  # type: ignore[arg-type]
            mode="live",
        )
        assert display.schema_version == "1.0"

    def test_mode_literal_validation(self) -> None:
        """Test mode must be 'live' or 'paper'."""
        account_info = {
            "account_id": "test",
            "equity": Decimal("1000"),
            "cash": Decimal("500"),
            "buying_power": Decimal("800"),
            "day_trades_remaining": 3,
            "portfolio_value": Decimal("1000"),
            "last_equity": Decimal("950"),
            "daytrading_buying_power": Decimal("800"),
            "regt_buying_power": Decimal("700"),
            "status": "ACTIVE",
        }

        with pytest.raises(ValidationError) as exc_info:
            CLIAccountDisplay(
                account_info=account_info,  # type: ignore[arg-type]
                mode="invalid",  # type: ignore[arg-type]
            )

        assert "Input should be 'live' or 'paper'" in str(exc_info.value)


class TestCLIPortfolioData:
    """Test CLI portfolio data schema validation."""

    def test_valid_portfolio_data(self) -> None:
        """Test creating valid portfolio data with Decimal values."""
        portfolio = CLIPortfolioData(
            symbol="AAPL",
            allocation_percentage=Decimal("25.5"),
            current_value=Decimal("5000.00"),
            target_value=Decimal("5500.00"),
        )

        assert portfolio.symbol == "AAPL"
        assert portfolio.allocation_percentage == Decimal("25.5")
        assert portfolio.current_value == Decimal("5000.00")
        assert portfolio.target_value == Decimal("5500.00")

    def test_schema_version(self) -> None:
        """Test schema version is included and defaults to 1.0."""
        portfolio = CLIPortfolioData(
            symbol="AAPL",
            allocation_percentage=Decimal("25.5"),
            current_value=Decimal("5000.00"),
            target_value=Decimal("5500.00"),
        )
        assert portfolio.schema_version == "1.0"

    def test_allocation_percentage_lower_bound(self) -> None:
        """Test allocation percentage cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            CLIPortfolioData(
                symbol="AAPL",
                allocation_percentage=Decimal("-1.0"),
                current_value=Decimal("5000.00"),
                target_value=Decimal("5500.00"),
            )

        assert "greater than or equal to 0" in str(exc_info.value)

    def test_allocation_percentage_upper_bound(self) -> None:
        """Test allocation percentage cannot exceed 100."""
        with pytest.raises(ValidationError) as exc_info:
            CLIPortfolioData(
                symbol="AAPL",
                allocation_percentage=Decimal("101.0"),
                current_value=Decimal("5000.00"),
                target_value=Decimal("5500.00"),
            )

        assert "less than or equal to 100" in str(exc_info.value)

    def test_allocation_percentage_boundary_values(self) -> None:
        """Test allocation percentage boundary values 0 and 100."""
        portfolio_min = CLIPortfolioData(
            symbol="AAPL",
            allocation_percentage=Decimal("0"),
            current_value=Decimal("0"),
            target_value=Decimal("0"),
        )
        portfolio_max = CLIPortfolioData(
            symbol="AAPL",
            allocation_percentage=Decimal("100"),
            current_value=Decimal("10000.00"),
            target_value=Decimal("10000.00"),
        )

        assert portfolio_min.allocation_percentage == Decimal("0")
        assert portfolio_max.allocation_percentage == Decimal("100")

    def test_decimal_precision_maintained(self) -> None:
        """Test that Decimal precision is maintained (no float conversion)."""
        portfolio = CLIPortfolioData(
            symbol="AAPL",
            allocation_percentage=Decimal("33.333333"),
            current_value=Decimal("1234.567890"),
            target_value=Decimal("9876.543210"),
        )

        # Verify precision is maintained
        assert isinstance(portfolio.allocation_percentage, Decimal)
        assert isinstance(portfolio.current_value, Decimal)
        assert isinstance(portfolio.target_value, Decimal)
        assert str(portfolio.allocation_percentage) == "33.333333"
        assert str(portfolio.current_value) == "1234.567890"

    def test_immutability(self) -> None:
        """Test that CLIPortfolioData is frozen and immutable."""
        portfolio = CLIPortfolioData(
            symbol="AAPL",
            allocation_percentage=Decimal("25.5"),
            current_value=Decimal("5000.00"),
            target_value=Decimal("5500.00"),
        )

        with pytest.raises(ValidationError):
            portfolio.symbol = "GOOGL"  # type: ignore[misc]


class TestCLIOrderDisplay:
    """Test CLI order display schema validation."""

    def test_valid_order_display(self) -> None:
        """Test creating valid order display data."""
        order_details = {
            "id": "order123",
            "symbol": "AAPL",
            "qty": Decimal("10"),
            "side": "buy",
            "order_type": "market",
            "time_in_force": "day",
            "status": "filled",
            "filled_qty": Decimal("10"),
            "filled_avg_price": Decimal("150.00"),
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-15T10:00:01Z",
        }

        display = CLIOrderDisplay(
            order_details=order_details,  # type: ignore[arg-type]
            display_style="detailed",
            formatted_amount="$1,500.00",
        )

        assert display.display_style == "detailed"
        assert display.formatted_amount == "$1,500.00"
        assert display.order_details["symbol"] == "AAPL"  # type: ignore[index]

    def test_schema_version(self) -> None:
        """Test schema version is included and defaults to 1.0."""
        order_details = {
            "id": "order123",
            "symbol": "AAPL",
            "qty": Decimal("10"),
            "side": "buy",
            "order_type": "market",
            "time_in_force": "day",
            "status": "filled",
            "filled_qty": Decimal("10"),
            "filled_avg_price": Decimal("150.00"),
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-15T10:00:01Z",
        }

        display = CLIOrderDisplay(
            order_details=order_details,  # type: ignore[arg-type]
            display_style="compact",
            formatted_amount="$1.5K",
        )
        assert display.schema_version == "1.0"

    def test_immutability(self) -> None:
        """Test that CLIOrderDisplay is frozen and immutable."""
        order_details = {
            "id": "order123",
            "symbol": "AAPL",
            "qty": Decimal("10"),
            "side": "buy",
            "order_type": "market",
            "time_in_force": "day",
            "status": "filled",
            "filled_qty": Decimal("10"),
            "filled_avg_price": Decimal("150.00"),
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-15T10:00:01Z",
        }

        display = CLIOrderDisplay(
            order_details=order_details,  # type: ignore[arg-type]
            display_style="detailed",
            formatted_amount="$1,500.00",
        )

        with pytest.raises(ValidationError):
            display.display_style = "compact"  # type: ignore[misc]
