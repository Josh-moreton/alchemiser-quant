"""Business Unit: shared | Status: current.

Comprehensive unit and property-based tests for account schema DTOs.

Tests all account-related DTOs with validation, immutability, and constraint checks.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from the_alchemiser.shared.schemas.accounts import (
    AccountMetrics,
    AccountSummary,
    BuyingPowerResult,
    EnrichedAccountSummaryView,
    PortfolioAllocationResult,
    RiskMetrics,
    RiskMetricsResult,
    TradeEligibilityResult,
)


class TestAccountMetrics:
    """Test AccountMetrics DTO."""

    @pytest.mark.unit
    def test_create_valid_account_metrics(self):
        """Test creating valid AccountMetrics."""
        metrics = AccountMetrics(
            cash_ratio=Decimal("0.5"),
            market_exposure=Decimal("0.5"),
            leverage_ratio=Decimal("1.0"),
            available_buying_power_ratio=Decimal("1.0"),
        )

        assert metrics.cash_ratio == Decimal("0.5")
        assert metrics.market_exposure == Decimal("0.5")
        assert metrics.leverage_ratio == Decimal("1.0")
        assert metrics.available_buying_power_ratio == Decimal("1.0")
        assert metrics.schema_version == "1.0"

    @pytest.mark.unit
    def test_account_metrics_is_frozen(self):
        """Test that AccountMetrics is immutable."""
        metrics = AccountMetrics(
            cash_ratio=Decimal("0.5"),
            market_exposure=Decimal("0.5"),
            leverage_ratio=None,
            available_buying_power_ratio=Decimal("1.0"),
        )

        with pytest.raises(ValidationError):
            metrics.cash_ratio = Decimal("0.8")

    @pytest.mark.unit
    def test_cash_ratio_must_be_between_0_and_1(self):
        """Test cash_ratio validation bounds."""
        # Valid: 0
        metrics = AccountMetrics(
            cash_ratio=Decimal("0"),
            market_exposure=Decimal("1.0"),
            leverage_ratio=None,
            available_buying_power_ratio=Decimal("1.0"),
        )
        assert metrics.cash_ratio == Decimal("0")

        # Valid: 1
        metrics = AccountMetrics(
            cash_ratio=Decimal("1"),
            market_exposure=Decimal("0"),
            leverage_ratio=None,
            available_buying_power_ratio=Decimal("1.0"),
        )
        assert metrics.cash_ratio == Decimal("1")

        # Invalid: > 1
        with pytest.raises(ValidationError) as exc_info:
            AccountMetrics(
                cash_ratio=Decimal("1.5"),
                market_exposure=Decimal("0.5"),
                leverage_ratio=None,
                available_buying_power_ratio=Decimal("1.0"),
            )
        assert "cash_ratio" in str(exc_info.value)

        # Invalid: < 0
        with pytest.raises(ValidationError) as exc_info:
            AccountMetrics(
                cash_ratio=Decimal("-0.1"),
                market_exposure=Decimal("0.5"),
                leverage_ratio=None,
                available_buying_power_ratio=Decimal("1.0"),
            )
        assert "cash_ratio" in str(exc_info.value)

    @pytest.mark.unit
    def test_market_exposure_must_be_non_negative(self):
        """Test market_exposure validation."""
        # Valid: 0
        metrics = AccountMetrics(
            cash_ratio=Decimal("1.0"),
            market_exposure=Decimal("0"),
            leverage_ratio=None,
            available_buying_power_ratio=Decimal("1.0"),
        )
        assert metrics.market_exposure == Decimal("0")

        # Invalid: negative
        with pytest.raises(ValidationError) as exc_info:
            AccountMetrics(
                cash_ratio=Decimal("0.5"),
                market_exposure=Decimal("-0.5"),
                leverage_ratio=None,
                available_buying_power_ratio=Decimal("1.0"),
            )
        assert "market_exposure" in str(exc_info.value)

    @pytest.mark.unit
    def test_leverage_ratio_can_be_none(self):
        """Test that leverage_ratio can be None for cash accounts."""
        metrics = AccountMetrics(
            cash_ratio=Decimal("1.0"),
            market_exposure=Decimal("0"),
            leverage_ratio=None,
            available_buying_power_ratio=Decimal("1.0"),
        )
        assert metrics.leverage_ratio is None


class TestAccountSummary:
    """Test AccountSummary DTO."""

    @pytest.fixture
    def valid_metrics(self):
        """Create valid AccountMetrics for testing."""
        return AccountMetrics(
            cash_ratio=Decimal("0.5"),
            market_exposure=Decimal("0.5"),
            leverage_ratio=None,
            available_buying_power_ratio=Decimal("1.0"),
        )

    @pytest.mark.unit
    def test_create_valid_account_summary(self, valid_metrics):
        """Test creating valid AccountSummary."""
        summary = AccountSummary(
            account_id="test-account-123",
            equity=Decimal("10000.00"),
            cash=Decimal("5000.00"),
            market_value=Decimal("5000.00"),
            buying_power=Decimal("10000.00"),
            last_equity=Decimal("9500.00"),
            day_trade_count=2,
            pattern_day_trader=False,
            trading_blocked=False,
            transfers_blocked=False,
            account_blocked=False,
            calculated_metrics=valid_metrics,
        )

        assert summary.account_id == "test-account-123"
        assert summary.equity == Decimal("10000.00")
        assert summary.cash == Decimal("5000.00")
        assert summary.schema_version == "1.0"

    @pytest.mark.unit
    def test_account_summary_is_frozen(self, valid_metrics):
        """Test that AccountSummary is immutable."""
        summary = AccountSummary(
            account_id="test-123",
            equity=Decimal("10000.00"),
            cash=Decimal("5000.00"),
            market_value=Decimal("5000.00"),
            buying_power=Decimal("10000.00"),
            last_equity=Decimal("9500.00"),
            day_trade_count=2,
            pattern_day_trader=False,
            trading_blocked=False,
            transfers_blocked=False,
            account_blocked=False,
            calculated_metrics=valid_metrics,
        )

        with pytest.raises(ValidationError):
            summary.equity = Decimal("20000.00")

    @pytest.mark.unit
    def test_account_id_cannot_be_empty(self, valid_metrics):
        """Test that account_id must have minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            AccountSummary(
                account_id="",
                equity=Decimal("10000.00"),
                cash=Decimal("5000.00"),
                market_value=Decimal("5000.00"),
                buying_power=Decimal("10000.00"),
                last_equity=Decimal("9500.00"),
                day_trade_count=2,
                pattern_day_trader=False,
                trading_blocked=False,
                transfers_blocked=False,
                account_blocked=False,
                calculated_metrics=valid_metrics,
            )
        assert "account_id" in str(exc_info.value)

    @pytest.mark.unit
    def test_financial_fields_must_be_non_negative(self, valid_metrics):
        """Test that financial fields cannot be negative."""
        # Test negative equity
        with pytest.raises(ValidationError) as exc_info:
            AccountSummary(
                account_id="test-123",
                equity=Decimal("-1000.00"),
                cash=Decimal("5000.00"),
                market_value=Decimal("5000.00"),
                buying_power=Decimal("10000.00"),
                last_equity=Decimal("9500.00"),
                day_trade_count=2,
                pattern_day_trader=False,
                trading_blocked=False,
                transfers_blocked=False,
                account_blocked=False,
                calculated_metrics=valid_metrics,
            )
        assert "equity" in str(exc_info.value)

        # Test negative cash
        with pytest.raises(ValidationError) as exc_info:
            AccountSummary(
                account_id="test-123",
                equity=Decimal("10000.00"),
                cash=Decimal("-100.00"),
                market_value=Decimal("5000.00"),
                buying_power=Decimal("10000.00"),
                last_equity=Decimal("9500.00"),
                day_trade_count=2,
                pattern_day_trader=False,
                trading_blocked=False,
                transfers_blocked=False,
                account_blocked=False,
                calculated_metrics=valid_metrics,
            )
        assert "cash" in str(exc_info.value)

    @pytest.mark.unit
    def test_day_trade_count_must_be_non_negative(self, valid_metrics):
        """Test that day_trade_count cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            AccountSummary(
                account_id="test-123",
                equity=Decimal("10000.00"),
                cash=Decimal("5000.00"),
                market_value=Decimal("5000.00"),
                buying_power=Decimal("10000.00"),
                last_equity=Decimal("9500.00"),
                day_trade_count=-1,
                pattern_day_trader=False,
                trading_blocked=False,
                transfers_blocked=False,
                account_blocked=False,
                calculated_metrics=valid_metrics,
            )
        assert "day_trade_count" in str(exc_info.value)


class TestBuyingPowerResult:
    """Test BuyingPowerResult DTO."""

    @pytest.mark.unit
    def test_create_valid_buying_power_result(self):
        """Test creating valid BuyingPowerResult."""
        result = BuyingPowerResult(
            success=True,
            error=None,
            available_buying_power=Decimal("10000.00"),
            required_amount=Decimal("5000.00"),
            sufficient_funds=True,
        )

        assert result.success is True
        assert result.available_buying_power == Decimal("10000.00")
        assert result.sufficient_funds is True
        assert result.schema_version == "1.0"

    @pytest.mark.unit
    def test_buying_power_result_is_frozen(self):
        """Test that BuyingPowerResult is immutable."""
        result = BuyingPowerResult(
            success=True,
            error=None,
            available_buying_power=Decimal("10000.00"),
            required_amount=Decimal("5000.00"),
            sufficient_funds=True,
        )

        with pytest.raises(ValidationError):
            result.success = False

    @pytest.mark.unit
    def test_buying_power_amounts_must_be_non_negative(self):
        """Test that amounts cannot be negative."""
        # Negative available_buying_power
        with pytest.raises(ValidationError) as exc_info:
            BuyingPowerResult(
                success=False,
                error="Insufficient funds",
                available_buying_power=Decimal("-100.00"),
                required_amount=Decimal("5000.00"),
                sufficient_funds=False,
            )
        assert "available_buying_power" in str(exc_info.value)

        # Negative required_amount
        with pytest.raises(ValidationError) as exc_info:
            BuyingPowerResult(
                success=True,
                error=None,
                available_buying_power=Decimal("10000.00"),
                required_amount=Decimal("-5000.00"),
                sufficient_funds=True,
            )
        assert "required_amount" in str(exc_info.value)

    @pytest.mark.unit
    def test_optional_fields_can_be_none(self):
        """Test that optional fields can be None."""
        result = BuyingPowerResult(
            success=False,
            error="Service unavailable",
            available_buying_power=None,
            required_amount=None,
            sufficient_funds=None,
        )

        assert result.available_buying_power is None
        assert result.required_amount is None
        assert result.sufficient_funds is None


class TestRiskMetrics:
    """Test RiskMetrics DTO."""

    @pytest.mark.unit
    def test_create_valid_risk_metrics(self):
        """Test creating valid RiskMetrics."""
        metrics = RiskMetrics(
            max_position_size=Decimal("5000.00"),
            concentration_limit=Decimal("0.2"),
            total_exposure=Decimal("0.8"),
            risk_score=Decimal("7.5"),
        )

        assert metrics.max_position_size == Decimal("5000.00")
        assert metrics.concentration_limit == Decimal("0.2")
        assert metrics.total_exposure == Decimal("0.8")
        assert metrics.risk_score == Decimal("7.5")
        assert metrics.schema_version == "1.0"

    @pytest.mark.unit
    def test_risk_metrics_is_frozen(self):
        """Test that RiskMetrics is immutable."""
        metrics = RiskMetrics(
            max_position_size=Decimal("5000.00"),
            concentration_limit=Decimal("0.2"),
            total_exposure=Decimal("0.8"),
            risk_score=Decimal("7.5"),
        )

        with pytest.raises(ValidationError):
            metrics.risk_score = Decimal("10.0")

    @pytest.mark.unit
    def test_concentration_limit_must_be_between_0_and_1(self):
        """Test concentration_limit validation bounds."""
        # Valid: 0
        metrics = RiskMetrics(
            max_position_size=Decimal("5000.00"),
            concentration_limit=Decimal("0"),
            total_exposure=Decimal("0.8"),
            risk_score=Decimal("7.5"),
        )
        assert metrics.concentration_limit == Decimal("0")

        # Valid: 1
        metrics = RiskMetrics(
            max_position_size=Decimal("5000.00"),
            concentration_limit=Decimal("1"),
            total_exposure=Decimal("0.8"),
            risk_score=Decimal("7.5"),
        )
        assert metrics.concentration_limit == Decimal("1")

        # Invalid: > 1
        with pytest.raises(ValidationError) as exc_info:
            RiskMetrics(
                max_position_size=Decimal("5000.00"),
                concentration_limit=Decimal("1.5"),
                total_exposure=Decimal("0.8"),
                risk_score=Decimal("7.5"),
            )
        assert "concentration_limit" in str(exc_info.value)

    @pytest.mark.unit
    def test_all_fields_must_be_non_negative(self):
        """Test that all numeric fields must be non-negative."""
        # Negative max_position_size
        with pytest.raises(ValidationError) as exc_info:
            RiskMetrics(
                max_position_size=Decimal("-100.00"),
                concentration_limit=Decimal("0.2"),
                total_exposure=Decimal("0.8"),
                risk_score=Decimal("7.5"),
            )
        assert "max_position_size" in str(exc_info.value)


class TestRiskMetricsResult:
    """Test RiskMetricsResult DTO."""

    @pytest.mark.unit
    def test_create_valid_risk_metrics_result(self):
        """Test creating valid RiskMetricsResult."""
        metrics = RiskMetrics(
            max_position_size=Decimal("5000.00"),
            concentration_limit=Decimal("0.2"),
            total_exposure=Decimal("0.8"),
            risk_score=Decimal("7.5"),
        )
        result = RiskMetricsResult(
            success=True,
            error=None,
            risk_metrics=metrics,
        )

        assert result.success is True
        assert result.risk_metrics is not None
        assert result.risk_metrics.risk_score == Decimal("7.5")
        assert result.schema_version == "1.0"

    @pytest.mark.unit
    def test_risk_metrics_result_is_frozen(self):
        """Test that RiskMetricsResult is immutable."""
        result = RiskMetricsResult(
            success=True,
            error=None,
            risk_metrics=None,
        )

        with pytest.raises(ValidationError):
            result.success = False

    @pytest.mark.unit
    def test_risk_metrics_can_be_none(self):
        """Test that risk_metrics can be None."""
        result = RiskMetricsResult(
            success=False,
            error="Failed to calculate risk metrics",
            risk_metrics=None,
        )

        assert result.risk_metrics is None


class TestTradeEligibilityResult:
    """Test TradeEligibilityResult DTO."""

    @pytest.mark.unit
    def test_create_valid_eligible_result(self):
        """Test creating valid eligible TradeEligibilityResult."""
        result = TradeEligibilityResult(
            eligible=True,
            reason=None,
            details=None,
            symbol="AAPL",
            quantity=Decimal("10"),
            side="BUY",
            estimated_cost=Decimal("1500.00"),
        )

        assert result.eligible is True
        assert result.symbol == "AAPL"
        assert result.quantity == Decimal("10")
        assert result.side == "BUY"
        assert result.schema_version == "1.0"

    @pytest.mark.unit
    def test_create_valid_ineligible_result(self):
        """Test creating valid ineligible TradeEligibilityResult."""
        result = TradeEligibilityResult(
            eligible=False,
            reason="Insufficient buying power",
            details={"available": "100.00", "required": "1500.00"},
            symbol="AAPL",
            quantity=Decimal("10"),
            side="BUY",
            estimated_cost=Decimal("1500.00"),
        )

        assert result.eligible is False
        assert result.reason == "Insufficient buying power"
        assert result.details is not None

    @pytest.mark.unit
    def test_trade_eligibility_result_is_frozen(self):
        """Test that TradeEligibilityResult is immutable."""
        result = TradeEligibilityResult(
            eligible=True,
            symbol="AAPL",
            quantity=Decimal("10"),
            side="BUY",
            estimated_cost=Decimal("1500.00"),
        )

        with pytest.raises(ValidationError):
            result.eligible = False

    @pytest.mark.unit
    def test_side_must_be_buy_or_sell(self):
        """Test that side must be BUY or SELL."""
        # Valid: BUY
        result = TradeEligibilityResult(
            eligible=True,
            side="BUY",
            quantity=Decimal("10"),
            estimated_cost=Decimal("1500.00"),
        )
        assert result.side == "BUY"

        # Valid: SELL
        result = TradeEligibilityResult(
            eligible=True,
            side="SELL",
            quantity=Decimal("10"),
            estimated_cost=Decimal("1500.00"),
        )
        assert result.side == "SELL"

        # Invalid: other value
        with pytest.raises(ValidationError) as exc_info:
            TradeEligibilityResult(
                eligible=True,
                side="HOLD",
                quantity=Decimal("10"),
                estimated_cost=Decimal("1500.00"),
            )
        assert "side" in str(exc_info.value)

    @pytest.mark.unit
    def test_quantity_must_be_positive_decimal(self):
        """Test that quantity must be positive Decimal."""
        # Valid: positive Decimal
        result = TradeEligibilityResult(
            eligible=True,
            quantity=Decimal("10.5"),
            estimated_cost=Decimal("1500.00"),
        )
        assert result.quantity == Decimal("10.5")

        # Invalid: zero
        with pytest.raises(ValidationError) as exc_info:
            TradeEligibilityResult(
                eligible=True,
                quantity=Decimal("0"),
                estimated_cost=Decimal("1500.00"),
            )
        assert "quantity" in str(exc_info.value)

        # Invalid: negative
        with pytest.raises(ValidationError) as exc_info:
            TradeEligibilityResult(
                eligible=True,
                quantity=Decimal("-10"),
                estimated_cost=Decimal("1500.00"),
            )
        assert "quantity" in str(exc_info.value)

    @pytest.mark.unit
    def test_symbol_validation(self):
        """Test symbol validation constraints."""
        # Valid symbol
        result = TradeEligibilityResult(
            eligible=True,
            symbol="AAPL",
            quantity=Decimal("10"),
            estimated_cost=Decimal("1500.00"),
        )
        assert result.symbol == "AAPL"

        # Invalid: empty string
        with pytest.raises(ValidationError) as exc_info:
            TradeEligibilityResult(
                eligible=True,
                symbol="",
                quantity=Decimal("10"),
                estimated_cost=Decimal("1500.00"),
            )
        assert "symbol" in str(exc_info.value)

        # Invalid: too long
        with pytest.raises(ValidationError) as exc_info:
            TradeEligibilityResult(
                eligible=True,
                symbol="TOOLONGSYMBOL",
                quantity=Decimal("10"),
                estimated_cost=Decimal("1500.00"),
            )
        assert "symbol" in str(exc_info.value)


class TestPortfolioAllocationResult:
    """Test PortfolioAllocationResult DTO."""

    @pytest.mark.unit
    def test_create_valid_portfolio_allocation_result(self):
        """Test creating valid PortfolioAllocationResult."""
        allocation = {
            "AAPL": {"weight": 0.3, "value": 3000.00},
            "GOOGL": {"weight": 0.3, "value": 3000.00},
            "MSFT": {"weight": 0.4, "value": 4000.00},
        }
        result = PortfolioAllocationResult(
            success=True,
            error=None,
            allocation_data=allocation,
        )

        assert result.success is True
        assert result.allocation_data is not None
        assert "AAPL" in result.allocation_data
        assert result.schema_version == "1.0"

    @pytest.mark.unit
    def test_portfolio_allocation_result_is_frozen(self):
        """Test that PortfolioAllocationResult is immutable."""
        result = PortfolioAllocationResult(
            success=True,
            error=None,
            allocation_data={},
        )

        with pytest.raises(ValidationError):
            result.success = False

    @pytest.mark.unit
    def test_allocation_data_can_be_none(self):
        """Test that allocation_data can be None."""
        result = PortfolioAllocationResult(
            success=False,
            error="Failed to calculate allocation",
            allocation_data=None,
        )

        assert result.allocation_data is None


class TestEnrichedAccountSummaryView:
    """Test EnrichedAccountSummaryView DTO."""

    @pytest.fixture
    def valid_account_summary(self):
        """Create valid AccountSummary for testing."""
        metrics = AccountMetrics(
            cash_ratio=Decimal("0.5"),
            market_exposure=Decimal("0.5"),
            leverage_ratio=None,
            available_buying_power_ratio=Decimal("1.0"),
        )
        return AccountSummary(
            account_id="test-123",
            equity=Decimal("10000.00"),
            cash=Decimal("5000.00"),
            market_value=Decimal("5000.00"),
            buying_power=Decimal("10000.00"),
            last_equity=Decimal("9500.00"),
            day_trade_count=2,
            pattern_day_trader=False,
            trading_blocked=False,
            transfers_blocked=False,
            account_blocked=False,
            calculated_metrics=metrics,
        )

    @pytest.mark.unit
    def test_create_valid_enriched_account_summary(self, valid_account_summary):
        """Test creating valid EnrichedAccountSummaryView."""
        raw_data = {
            "account_number": "test-123",
            "equity": "10000.00",
            "cash": "5000.00",
        }
        view = EnrichedAccountSummaryView(
            raw=raw_data,
            summary=valid_account_summary,
        )

        assert view.raw == raw_data
        assert view.summary.account_id == "test-123"
        assert view.schema_version == "1.0"

    @pytest.mark.unit
    def test_enriched_account_summary_is_frozen(self, valid_account_summary):
        """Test that EnrichedAccountSummaryView is immutable."""
        view = EnrichedAccountSummaryView(
            raw={},
            summary=valid_account_summary,
        )

        with pytest.raises(ValidationError):
            view.raw = {"new": "data"}


# Property-based tests using Hypothesis
class TestAccountMetricsProperties:
    """Property-based tests for AccountMetrics."""

    @given(
        cash_ratio=st.decimals(min_value=Decimal("0"), max_value=Decimal("1"), places=4),
        market_exposure=st.decimals(min_value=Decimal("0"), max_value=Decimal("2"), places=4),
        available_buying_power_ratio=st.decimals(
            min_value=Decimal("0"), max_value=Decimal("5"), places=4
        ),
    )
    def test_account_metrics_roundtrip(
        self, cash_ratio, market_exposure, available_buying_power_ratio
    ):
        """Test that AccountMetrics can be created with valid random values."""
        metrics = AccountMetrics(
            cash_ratio=cash_ratio,
            market_exposure=market_exposure,
            leverage_ratio=None,
            available_buying_power_ratio=available_buying_power_ratio,
        )

        # Verify all fields are preserved
        assert metrics.cash_ratio == cash_ratio
        assert metrics.market_exposure == market_exposure
        assert metrics.available_buying_power_ratio == available_buying_power_ratio


class TestAccountSummaryProperties:
    """Property-based tests for AccountSummary."""

    @given(
        equity=st.decimals(min_value=Decimal("0"), max_value=Decimal("1000000"), places=2),
        cash=st.decimals(min_value=Decimal("0"), max_value=Decimal("1000000"), places=2),
        day_trade_count=st.integers(min_value=0, max_value=100),
    )
    def test_account_summary_with_random_valid_values(self, equity, cash, day_trade_count):
        """Test AccountSummary with random valid values."""
        metrics = AccountMetrics(
            cash_ratio=Decimal("0.5"),
            market_exposure=Decimal("0.5"),
            leverage_ratio=None,
            available_buying_power_ratio=Decimal("1.0"),
        )

        summary = AccountSummary(
            account_id="test-account",
            equity=equity,
            cash=cash,
            market_value=Decimal("0"),
            buying_power=equity,
            last_equity=equity,
            day_trade_count=day_trade_count,
            pattern_day_trader=False,
            trading_blocked=False,
            transfers_blocked=False,
            account_blocked=False,
            calculated_metrics=metrics,
        )

        # Verify all fields are preserved
        assert summary.equity == equity
        assert summary.cash == cash
        assert summary.day_trade_count == day_trade_count
