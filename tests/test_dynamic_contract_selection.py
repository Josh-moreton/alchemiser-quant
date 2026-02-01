"""Business Unit: shared | Status: current.

pytest tests for dynamic options contract selection.

Tests tenor selector and convexity selector functionality.
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from the_alchemiser.shared.options.convexity_selector import ConvexitySelector
from the_alchemiser.shared.options.schemas import OptionContract, OptionType
from the_alchemiser.shared.options.tenor_selector import TenorSelector


class TestTenorSelector:
    """Tests for TenorSelector."""

    @pytest.fixture
    def selector(self) -> TenorSelector:
        """Create a TenorSelector instance."""
        return TenorSelector()

    def test_low_vix_with_ladder_returns_ladder_strategy(
        self, selector: TenorSelector
    ) -> None:
        """Test that low VIX with ladder enabled returns ladder strategy."""
        rec = selector.select_tenor(
            current_vix=Decimal("15"),
            use_ladder=True,
        )

        assert rec.strategy == "ladder"
        assert rec.primary_dte == 75  # Midpoint of 60-90 range
        assert rec.secondary_dte == 150  # Midpoint of 120-180 range
        assert "ladder" in rec.rationale.lower()

    def test_high_iv_percentile_returns_longer_tenor(
        self, selector: TenorSelector
    ) -> None:
        """Test that high IV percentile (>70%) selects longer tenors."""
        rec = selector.select_tenor(
            current_vix=Decimal("25"),
            iv_percentile=Decimal("0.75"),
            use_ladder=False,
        )

        assert rec.strategy == "single"
        assert rec.primary_dte == 150  # Midpoint of 120-180 range (long tenor)
        assert rec.secondary_dte is None
        assert "iv percentile" in rec.rationale.lower()

    def test_rich_vix_returns_longer_tenor(self, selector: TenorSelector) -> None:
        """Test that rich VIX (>35) selects longer tenors."""
        rec = selector.select_tenor(
            current_vix=Decimal("40"),
            use_ladder=False,
        )

        assert rec.strategy == "single"
        assert rec.primary_dte == 150  # Midpoint of 120-180 range
        assert rec.secondary_dte is None
        assert "rich vix" in rec.rationale.lower()

    def test_high_iv_takes_precedence_over_ladder(
        self, selector: TenorSelector
    ) -> None:
        """Test that high IV percentile takes precedence over ladder."""
        rec = selector.select_tenor(
            current_vix=Decimal("25"),
            iv_percentile=Decimal("0.80"),
            use_ladder=True,
        )

        # High IV should select long tenor, not ladder
        assert rec.strategy == "single"
        assert rec.primary_dte == 150

    def test_low_vix_without_ladder_returns_short_tenor(
        self, selector: TenorSelector
    ) -> None:
        """Test that low VIX without ladder returns short tenor."""
        rec = selector.select_tenor(
            current_vix=Decimal("15"),
            use_ladder=False,
        )

        assert rec.strategy == "single"
        assert rec.primary_dte == 75  # Midpoint of 60-90 range


class TestConvexitySelector:
    """Tests for ConvexitySelector."""

    @pytest.fixture
    def selector(self) -> ConvexitySelector:
        """Create a ConvexitySelector instance."""
        return ConvexitySelector(
            scenario_move=Decimal("-0.20"),
            min_payoff_contribution=Decimal("3.0"),
        )

    @pytest.fixture
    def sample_contracts(self) -> list[OptionContract]:
        """Create sample contracts for testing."""
        expiry = date.today() + timedelta(days=90)
        return [
            # 15-delta put: strike 425 (15% OTM from $500)
            OptionContract(
                symbol="QQQ241231P425",
                underlying_symbol="QQQ",
                option_type=OptionType.PUT,
                strike_price=Decimal("425"),
                expiration_date=expiry,
                bid_price=Decimal("6.80"),
                ask_price=Decimal("7.00"),
                last_price=Decimal("6.90"),
                volume=500,
                open_interest=2000,
                delta=Decimal("-0.15"),
                gamma=Decimal("0.008"),
                theta=Decimal("-0.05"),
                vega=Decimal("0.50"),
                implied_volatility=Decimal("0.25"),
            ),
            # 10-delta put: strike 400 (20% OTM)
            OptionContract(
                symbol="QQQ241231P400",
                underlying_symbol="QQQ",
                option_type=OptionType.PUT,
                strike_price=Decimal("400"),
                expiration_date=expiry,
                bid_price=Decimal("4.50"),
                ask_price=Decimal("4.70"),
                last_price=Decimal("4.60"),
                volume=300,
                open_interest=1500,
                delta=Decimal("-0.10"),
                gamma=Decimal("0.006"),
                theta=Decimal("-0.03"),
                vega=Decimal("0.40"),
                implied_volatility=Decimal("0.27"),
            ),
            # 20-delta put: strike 450 (10% OTM)
            OptionContract(
                symbol="QQQ241231P450",
                underlying_symbol="QQQ",
                option_type=OptionType.PUT,
                strike_price=Decimal("450"),
                expiration_date=expiry,
                bid_price=Decimal("10.80"),
                ask_price=Decimal("11.00"),
                last_price=Decimal("10.90"),
                volume=800,
                open_interest=3000,
                delta=Decimal("-0.20"),
                gamma=Decimal("0.010"),
                theta=Decimal("-0.08"),
                vega=Decimal("0.60"),
                implied_volatility=Decimal("0.24"),
            ),
        ]

    def test_calculate_convexity_metrics(
        self, selector: ConvexitySelector, sample_contracts: list[OptionContract]
    ) -> None:
        """Test convexity metrics calculation."""
        underlying_price = Decimal("500")
        contract = sample_contracts[0]  # 15-delta put

        metrics = selector.calculate_convexity_metrics(contract, underlying_price)

        assert metrics is not None
        assert metrics.contract == contract
        assert metrics.convexity_per_dollar > Decimal("0")
        assert metrics.scenario_payoff_multiple > Decimal("0")
        assert metrics.effective_score > Decimal("0")

    def test_calculate_convexity_metrics_returns_none_without_gamma(
        self, selector: ConvexitySelector
    ) -> None:
        """Test that metrics returns None when gamma is missing."""
        expiry = date.today() + timedelta(days=90)
        contract = OptionContract(
            symbol="QQQ241231P425",
            underlying_symbol="QQQ",
            option_type=OptionType.PUT,
            strike_price=Decimal("425"),
            expiration_date=expiry,
            bid_price=Decimal("6.80"),
            ask_price=Decimal("7.00"),
            last_price=Decimal("6.90"),
            volume=500,
            open_interest=2000,
            delta=Decimal("-0.15"),
            gamma=None,  # No gamma data
        )

        metrics = selector.calculate_convexity_metrics(contract, Decimal("500"))

        assert metrics is None

    def test_filter_by_payoff_contribution(
        self, selector: ConvexitySelector, sample_contracts: list[OptionContract]
    ) -> None:
        """Test filtering contracts by minimum payoff contribution."""
        underlying_price = Decimal("500")

        # Calculate metrics for all contracts
        metrics_list = [
            selector.calculate_convexity_metrics(c, underlying_price)
            for c in sample_contracts
        ]
        metrics_list = [m for m in metrics_list if m is not None]

        # Filter by payoff contribution
        filtered = selector.filter_by_payoff_contribution(metrics_list)

        # All filtered contracts should have payoff >= 3x
        for m in filtered:
            assert m.scenario_payoff_multiple >= Decimal("3.0")

    def test_rank_by_convexity(
        self, selector: ConvexitySelector, sample_contracts: list[OptionContract]
    ) -> None:
        """Test ranking contracts by effective convexity score."""
        underlying_price = Decimal("500")

        # Calculate metrics for all contracts
        metrics_list = [
            selector.calculate_convexity_metrics(c, underlying_price)
            for c in sample_contracts
        ]
        metrics_list = [m for m in metrics_list if m is not None]

        # Rank by convexity
        ranked = selector.rank_by_convexity(metrics_list)

        # Should be sorted by effective_score descending
        for i in range(len(ranked) - 1):
            assert ranked[i].effective_score >= ranked[i + 1].effective_score

    def test_higher_strike_has_higher_scenario_payoff(
        self, selector: ConvexitySelector, sample_contracts: list[OptionContract]
    ) -> None:
        """Test that higher strikes produce higher scenario payoffs at -20%."""
        underlying_price = Decimal("500")

        # Strike 450 (10% OTM) vs Strike 400 (20% OTM)
        # At -20% scenario ($400 underlying), 450 strike has $50 intrinsic, 400 strike has $0
        high_strike_contract = sample_contracts[2]  # 450 strike
        low_strike_contract = sample_contracts[1]  # 400 strike

        high_metrics = selector.calculate_convexity_metrics(
            high_strike_contract, underlying_price
        )
        low_metrics = selector.calculate_convexity_metrics(
            low_strike_contract, underlying_price
        )

        assert high_metrics is not None
        assert low_metrics is not None
        assert high_metrics.scenario_payoff_multiple > low_metrics.scenario_payoff_multiple

    def test_scenario_payoff_at_minus_20_percent(
        self, selector: ConvexitySelector
    ) -> None:
        """Test scenario payoff calculation at -20% move."""
        expiry = date.today() + timedelta(days=90)
        underlying_price = Decimal("500")

        # At -20%, underlying = $400
        # Strike at $450 → intrinsic = $50 per share = $5000 per contract
        # If mid price = $10.90, premium = $1090 per contract
        # Payoff multiple = 5000 / 1090 ≈ 4.59
        contract = OptionContract(
            symbol="QQQ241231P450",
            underlying_symbol="QQQ",
            option_type=OptionType.PUT,
            strike_price=Decimal("450"),
            expiration_date=expiry,
            bid_price=Decimal("10.80"),
            ask_price=Decimal("11.00"),
            volume=800,
            open_interest=3000,
            delta=Decimal("-0.20"),
            gamma=Decimal("0.010"),
        )

        metrics = selector.calculate_convexity_metrics(contract, underlying_price)

        assert metrics is not None
        # Expected: (450 - 400) * 100 / (10.90 * 100) = 5000 / 1090 ≈ 4.59
        expected_multiple = (Decimal("450") - Decimal("400")) * 100 / (Decimal("10.90") * 100)
        assert abs(metrics.scenario_payoff_multiple - expected_multiple) < Decimal("0.01")
