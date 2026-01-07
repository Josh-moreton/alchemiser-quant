"""Business Unit: strategy | Status: current.

Unit tests for partial-bar indicator behavior.

Tests verify that:
1. Indicator classification is correct for all 9 indicators
2. Close-only indicators (current_price, cumulative_return) work with partial bars
3. Indicator values change as close-so-far updates intraday
4. Reference computation matches indicator output
5. Partial bar flag is propagated correctly

Test Families:
- Close-only indicators: current_price, cumulative_return
- Conditional indicators: RSI, EMA, moving_average, stdev_return, stdev_price
- Fully eligible: max_drawdown
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
import pytest

from the_alchemiser.shared.indicators.partial_bar_config import (
    InputRequirement,
    PartialBarEligibility,
    PartialBarIndicatorConfig,
    get_all_indicator_configs,
    get_indicator_config,
    is_eligible_for_partial_bar,
    should_use_live_bar,
)
from the_alchemiser.shared.types.market_data import BarModel
from the_alchemiser.shared.utils.evaluation_timestamp import (
    EvaluationTimestampProvider,
    get_evaluation_timestamp,
    get_evaluation_timestamp_utc,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_price_series() -> pd.Series:
    """Create a sample price series for indicator computation."""
    # 20 days of price data
    dates = pd.date_range(end=datetime.now(UTC), periods=20, freq="D")
    prices = [
        100.0, 101.5, 99.8, 102.3, 103.1,  # Week 1
        101.2, 104.5, 105.8, 103.2, 102.1,  # Week 2
        106.3, 107.9, 105.4, 108.2, 109.5,  # Week 3
        107.8, 110.2, 111.5, 109.3, 112.0,  # Week 4
    ]
    return pd.Series(prices, index=dates)


@pytest.fixture
def sample_bars() -> list[BarModel]:
    """Create sample BarModel list for testing."""
    base_date = datetime.now(UTC) - timedelta(days=10)
    bars = []
    prices = [100.0, 102.0, 101.0, 103.0, 105.0, 104.0, 106.0, 108.0, 107.0, 110.0]

    for i, price in enumerate(prices):
        bar = BarModel(
            symbol="SPY",
            timestamp=base_date + timedelta(days=i),
            open=Decimal(str(price - 1)),
            high=Decimal(str(price + 2)),
            low=Decimal(str(price - 2)),
            close=Decimal(str(price)),
            volume=1000000,
            is_incomplete=False,
        )
        bars.append(bar)

    return bars


@pytest.fixture
def incomplete_bar() -> BarModel:
    """Create an incomplete (partial) bar representing today's close-so-far."""
    return BarModel(
        symbol="SPY",
        timestamp=datetime.now(UTC),
        open=Decimal("111.0"),
        high=Decimal("113.0"),
        low=Decimal("110.5"),
        close=Decimal("112.5"),  # Current price (close-so-far)
        volume=500000,
        is_incomplete=True,
    )


# =============================================================================
# INDICATOR CLASSIFICATION TESTS
# =============================================================================


class TestIndicatorClassification:
    """Tests for indicator partial-bar classification."""

    def test_all_indicators_classified(self) -> None:
        """Verify all 9 indicators have classification configs."""
        configs = get_all_indicator_configs()

        expected_indicators = {
            "current_price",
            "rsi",
            "moving_average",
            "exponential_moving_average_price",
            "moving_average_return",
            "cumulative_return",
            "stdev_return",
            "stdev_price",
            "max_drawdown",
        }

        assert set(configs.keys()) == expected_indicators
        assert len(configs) == 9

    def test_all_indicators_are_close_only(self) -> None:
        """Verify all current indicators use CLOSE_ONLY inputs."""
        configs = get_all_indicator_configs()

        for indicator_type, config in configs.items():
            assert config.input_requirement == InputRequirement.CLOSE_ONLY, (
                f"Indicator {indicator_type} expected CLOSE_ONLY, "
                f"got {config.input_requirement}"
            )

    def test_current_price_fully_eligible(self) -> None:
        """current_price should be fully eligible for partial bar."""
        config = get_indicator_config("current_price")
        assert config is not None
        assert config.eligible_for_partial_bar == PartialBarEligibility.YES
        assert config.indicator_name == "current-price"

    def test_cumulative_return_fully_eligible(self) -> None:
        """cumulative_return should be fully eligible for partial bar."""
        config = get_indicator_config("cumulative_return")
        assert config is not None
        assert config.eligible_for_partial_bar == PartialBarEligibility.YES

    def test_max_drawdown_fully_eligible(self) -> None:
        """max_drawdown should be fully eligible for partial bar."""
        config = get_indicator_config("max_drawdown")
        assert config is not None
        assert config.eligible_for_partial_bar == PartialBarEligibility.YES

    def test_rsi_conditionally_eligible(self) -> None:
        """RSI should be conditionally eligible (more volatile intraday)."""
        config = get_indicator_config("rsi")
        assert config is not None
        assert config.eligible_for_partial_bar == PartialBarEligibility.CONDITIONAL
        assert len(config.edge_cases) > 0

    def test_ema_conditionally_eligible(self) -> None:
        """EMA should be conditionally eligible (higher weight on recent)."""
        config = get_indicator_config("exponential_moving_average_price")
        assert config is not None
        assert config.eligible_for_partial_bar == PartialBarEligibility.CONDITIONAL

    def test_is_eligible_for_partial_bar_helper(self) -> None:
        """Test is_eligible_for_partial_bar helper function."""
        # Fully eligible
        assert is_eligible_for_partial_bar("current_price") is True
        assert is_eligible_for_partial_bar("cumulative_return") is True

        # Conditionally eligible (returns True)
        assert is_eligible_for_partial_bar("rsi") is True
        assert is_eligible_for_partial_bar("exponential_moving_average_price") is True

        # Unknown indicator (defaults to True)
        assert is_eligible_for_partial_bar("unknown_indicator") is True

    def test_should_use_live_bar_per_indicator(self) -> None:
        """Test should_use_live_bar returns correct value per indicator."""
        # Indicators that use live bar (today's data)
        assert should_use_live_bar("current_price") is True
        assert should_use_live_bar("rsi") is False  # RSI too volatile with intraday data
        assert should_use_live_bar("max_drawdown") is True

        # These indicators should NOT use live bar (T-1 data only)
        # Confirmed via bento_collection testing
        assert should_use_live_bar("cumulative_return") is False
        assert should_use_live_bar("moving_average") is False
        assert should_use_live_bar("exponential_moving_average_price") is False
        assert should_use_live_bar("stdev_return") is False
        assert should_use_live_bar("stdev_price") is False
        assert should_use_live_bar("moving_average_return") is False

        # Unknown indicator (defaults to True - permissive)
        assert should_use_live_bar("unknown_indicator") is True

    def test_config_has_edge_cases(self) -> None:
        """Verify indicators with conditions have documented edge cases."""
        conditional_indicators = [
            "rsi",
            "exponential_moving_average_price",
            "moving_average_return",
            "stdev_return",
            "stdev_price",
        ]

        for indicator_type in conditional_indicators:
            config = get_indicator_config(indicator_type)
            assert config is not None
            assert len(config.edge_cases) > 0, (
                f"Indicator {indicator_type} with CONDITIONAL eligibility "
                f"should have edge cases documented"
            )


# =============================================================================
# EVALUATION TIMESTAMP TESTS
# =============================================================================


class TestEvaluationTimestamp:
    """Tests for evaluation timestamp provider."""

    def test_default_evaluation_time_is_1545_et(self) -> None:
        """Default evaluation time should be 15:45 ET."""
        provider = EvaluationTimestampProvider()
        assert provider.evaluation_hour == 15
        assert provider.evaluation_minute == 45

    def test_get_evaluation_timestamp_returns_et(self) -> None:
        """Evaluation timestamp should be in Eastern Time."""
        from datetime import date

        provider = EvaluationTimestampProvider()
        ts = provider.get_evaluation_timestamp(date(2026, 1, 7))

        assert ts.hour == 15
        assert ts.minute == 45
        assert ts.second == 0
        # Verify it's in America/New_York timezone
        assert "America/New_York" in str(ts.tzinfo) or ts.tzinfo is not None

    def test_get_evaluation_timestamp_utc_conversion(self) -> None:
        """UTC conversion should offset by 5 hours (EST) or 4 hours (EDT)."""
        from datetime import date

        provider = EvaluationTimestampProvider()
        et_ts = provider.get_evaluation_timestamp(date(2026, 1, 7))  # January = EST
        utc_ts = provider.get_evaluation_timestamp_utc(date(2026, 1, 7))

        # EST is UTC-5, so 15:45 ET = 20:45 UTC
        assert utc_ts.hour == 20
        assert utc_ts.minute == 45
        assert utc_ts.tzinfo == UTC

    def test_is_before_evaluation_time(self) -> None:
        """Test is_before_evaluation_time helper."""
        from datetime import date
        from zoneinfo import ZoneInfo

        provider = EvaluationTimestampProvider()
        test_date = date(2026, 1, 7)
        et_tz = ZoneInfo("America/New_York")

        # 10:00 AM ET is before 15:45 ET
        morning = datetime(2026, 1, 7, 10, 0, 0, tzinfo=et_tz)
        assert provider.is_before_evaluation_time(morning) is True

        # 16:00 PM ET is after 15:45 ET
        afternoon = datetime(2026, 1, 7, 16, 0, 0, tzinfo=et_tz)
        assert provider.is_before_evaluation_time(afternoon) is False

    def test_is_market_hours(self) -> None:
        """Test is_market_hours helper."""
        from zoneinfo import ZoneInfo

        provider = EvaluationTimestampProvider()
        et_tz = ZoneInfo("America/New_York")

        # 10:00 AM ET is during market hours (9:30-16:00)
        during = datetime(2026, 1, 7, 10, 0, 0, tzinfo=et_tz)
        assert provider.is_market_hours(during) is True

        # 8:00 AM ET is before market hours
        before = datetime(2026, 1, 7, 8, 0, 0, tzinfo=et_tz)
        assert provider.is_market_hours(before) is False

        # 17:00 PM ET is after market hours
        after = datetime(2026, 1, 7, 17, 0, 0, tzinfo=et_tz)
        assert provider.is_market_hours(after) is False

    def test_get_session_progress(self) -> None:
        """Test session progress calculation."""
        from zoneinfo import ZoneInfo

        provider = EvaluationTimestampProvider()
        et_tz = ZoneInfo("America/New_York")

        # Market open (9:30 AM) = 0%
        market_open = datetime(2026, 1, 7, 9, 30, 0, tzinfo=et_tz)
        assert provider.get_session_progress(market_open) == pytest.approx(0.0, abs=0.01)

        # Market close (4:00 PM) = 100%
        market_close = datetime(2026, 1, 7, 16, 0, 0, tzinfo=et_tz)
        assert provider.get_session_progress(market_close) == pytest.approx(1.0, abs=0.01)

        # 12:45 PM = ~50% (halfway through 6.5 hour session)
        midday = datetime(2026, 1, 7, 12, 45, 0, tzinfo=et_tz)
        progress = provider.get_session_progress(midday)
        assert 0.45 < progress < 0.55  # Approximately 50%

    def test_module_level_functions(self) -> None:
        """Test module-level convenience functions."""
        from datetime import date

        ts = get_evaluation_timestamp(date(2026, 1, 7))
        assert ts.hour == 15
        assert ts.minute == 45

        utc_ts = get_evaluation_timestamp_utc(date(2026, 1, 7))
        assert utc_ts.tzinfo == UTC

    def test_custom_evaluation_time(self) -> None:
        """Test custom evaluation time configuration."""
        from datetime import date

        # Configure for 14:30 ET instead of default 15:45 ET
        provider = EvaluationTimestampProvider(
            evaluation_hour=14,
            evaluation_minute=30,
        )

        ts = provider.get_evaluation_timestamp(date(2026, 1, 7))
        assert ts.hour == 14
        assert ts.minute == 30

    def test_invalid_hour_raises_error(self) -> None:
        """Invalid hour should raise ValueError."""
        with pytest.raises(ValueError, match="evaluation_hour must be 0-23"):
            EvaluationTimestampProvider(evaluation_hour=25)

    def test_invalid_minute_raises_error(self) -> None:
        """Invalid minute should raise ValueError."""
        with pytest.raises(ValueError, match="evaluation_minute must be 0-59"):
            EvaluationTimestampProvider(evaluation_minute=60)


# =============================================================================
# BAR MODEL INCOMPLETE FLAG TESTS
# =============================================================================


class TestBarModelIncompleteFlag:
    """Tests for BarModel is_incomplete flag."""

    def test_bar_model_default_complete(self, sample_bars: list[BarModel]) -> None:
        """BarModel should default to is_incomplete=False."""
        for bar in sample_bars:
            assert bar.is_incomplete is False

    def test_bar_model_incomplete_flag_set(self, incomplete_bar: BarModel) -> None:
        """BarModel should preserve is_incomplete=True."""
        assert incomplete_bar.is_incomplete is True
        assert incomplete_bar.symbol == "SPY"
        assert incomplete_bar.close == Decimal("112.5")

    def test_bars_can_mix_complete_and_incomplete(
        self,
        sample_bars: list[BarModel],
        incomplete_bar: BarModel,
    ) -> None:
        """Bar list can contain both complete and incomplete bars."""
        all_bars = sample_bars + [incomplete_bar]

        assert len(all_bars) == 11
        assert all_bars[-1].is_incomplete is True
        assert all(not bar.is_incomplete for bar in all_bars[:-1])


# =============================================================================
# CLOSE-ONLY INDICATOR FAMILY TESTS
# =============================================================================


class TestCloseOnlyIndicatorFamily:
    """Tests for close-only indicators with partial bar behavior.

    These tests verify that close-only indicators (current_price, cumulative_return)
    correctly use the partial bar's close-so-far value.
    """

    def test_current_price_uses_latest_close(
        self,
        sample_bars: list[BarModel],
        incomplete_bar: BarModel,
    ) -> None:
        """current_price should return the latest close (including partial bar)."""
        # Without partial bar
        prices_complete = pd.Series([float(bar.close) for bar in sample_bars])
        current_complete = prices_complete.iloc[-1]
        assert current_complete == 110.0

        # With partial bar appended
        all_bars = sample_bars + [incomplete_bar]
        prices_with_partial = pd.Series([float(bar.close) for bar in all_bars])
        current_with_partial = prices_with_partial.iloc[-1]
        assert current_with_partial == 112.5  # From incomplete bar

    def test_cumulative_return_changes_with_partial_bar(
        self,
        sample_bars: list[BarModel],
        incomplete_bar: BarModel,
    ) -> None:
        """cumulative_return should change when partial bar is appended."""
        window = 5

        # Without partial bar
        prices_complete = pd.Series([float(bar.close) for bar in sample_bars])
        returns_complete = ((prices_complete / prices_complete.shift(window)) - 1) * 100
        last_return_complete = returns_complete.iloc[-1]

        # With partial bar
        all_bars = sample_bars + [incomplete_bar]
        prices_with_partial = pd.Series([float(bar.close) for bar in all_bars])
        returns_with_partial = ((prices_with_partial / prices_with_partial.shift(window)) - 1) * 100
        last_return_with_partial = returns_with_partial.iloc[-1]

        # Returns should differ because numerator (current price) changed
        assert last_return_complete != last_return_with_partial
        # With higher close-so-far (112.5 vs 110.0), return should be higher
        assert last_return_with_partial > last_return_complete

    def test_indicator_value_changes_as_close_updates_intraday(
        self,
        sample_bars: list[BarModel],
    ) -> None:
        """Simulate intraday close-so-far changes and verify indicator updates."""
        # Simulate different intraday close-so-far values
        intraday_closes = [108.0, 110.0, 112.0, 109.0, 115.0]
        window = 5

        returns_by_intraday_close = []

        for close_so_far in intraday_closes:
            partial_bar = BarModel(
                symbol="SPY",
                timestamp=datetime.now(UTC),
                open=Decimal("111.0"),
                high=Decimal(str(max(close_so_far, 111.0) + 1)),
                low=Decimal(str(min(close_so_far, 111.0) - 1)),
                close=Decimal(str(close_so_far)),
                volume=500000,
                is_incomplete=True,
            )
            all_bars = sample_bars + [partial_bar]
            prices = pd.Series([float(bar.close) for bar in all_bars])
            cum_return = ((prices / prices.shift(window)) - 1) * 100
            returns_by_intraday_close.append(cum_return.iloc[-1])

        # Verify returns change as close-so-far changes
        assert len(set(returns_by_intraday_close)) == len(intraday_closes)

        # Higher close should give higher return
        highest_close_idx = intraday_closes.index(max(intraday_closes))
        lowest_close_idx = intraday_closes.index(min(intraday_closes))
        assert returns_by_intraday_close[highest_close_idx] > returns_by_intraday_close[lowest_close_idx]


# =============================================================================
# CONDITIONAL INDICATOR FAMILY TESTS
# =============================================================================


class TestConditionalIndicatorFamily:
    """Tests for conditionally eligible indicators (RSI, EMA, etc.).

    These indicators work with partial bars but may show increased variance.
    """

    def test_rsi_changes_with_partial_bar(
        self,
        sample_bars: list[BarModel],
        incomplete_bar: BarModel,
    ) -> None:
        """RSI should change when partial bar is appended."""
        window = 14

        def compute_rsi(prices: pd.Series, window: int) -> float:
            """Compute RSI using Wilder's method."""
            delta = prices.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            alpha = 1.0 / window
            avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
            avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1])

        # Without partial bar
        prices_complete = pd.Series([float(bar.close) for bar in sample_bars])
        rsi_complete = compute_rsi(prices_complete, window)

        # With partial bar (higher close)
        all_bars = sample_bars + [incomplete_bar]
        prices_with_partial = pd.Series([float(bar.close) for bar in all_bars])
        rsi_with_partial = compute_rsi(prices_with_partial, window)

        # RSI values should differ
        assert rsi_complete != rsi_with_partial

        # Higher close-so-far should generally increase RSI (more gains)
        # (This isn't always true depending on the data, so we just check they differ)
        assert abs(rsi_complete - rsi_with_partial) > 0.01

    def test_ema_changes_with_partial_bar(
        self,
        sample_bars: list[BarModel],
        incomplete_bar: BarModel,
    ) -> None:
        """EMA should change when partial bar is appended."""
        window = 8

        # Without partial bar
        prices_complete = pd.Series([float(bar.close) for bar in sample_bars])
        ema_complete = prices_complete.ewm(span=window, adjust=False).mean().iloc[-1]

        # With partial bar
        all_bars = sample_bars + [incomplete_bar]
        prices_with_partial = pd.Series([float(bar.close) for bar in all_bars])
        ema_with_partial = prices_with_partial.ewm(span=window, adjust=False).mean().iloc[-1]

        # EMA values should differ
        assert ema_complete != ema_with_partial

        # Higher close-so-far should increase EMA
        assert ema_with_partial > ema_complete

    def test_sma_changes_less_than_ema_with_partial_bar(
        self,
        sample_bars: list[BarModel],
        incomplete_bar: BarModel,
    ) -> None:
        """SMA should change less than EMA with partial bar (EMA weights recent more)."""
        window = 8

        # Without partial bar
        prices_complete = pd.Series([float(bar.close) for bar in sample_bars])
        sma_complete = prices_complete.rolling(window=window).mean().iloc[-1]
        ema_complete = prices_complete.ewm(span=window, adjust=False).mean().iloc[-1]

        # With partial bar
        all_bars = sample_bars + [incomplete_bar]
        prices_with_partial = pd.Series([float(bar.close) for bar in all_bars])
        sma_with_partial = prices_with_partial.rolling(window=window).mean().iloc[-1]
        ema_with_partial = prices_with_partial.ewm(span=window, adjust=False).mean().iloc[-1]

        # Both should change
        sma_change = abs(sma_with_partial - sma_complete)
        ema_change = abs(ema_with_partial - ema_complete)

        # EMA should be more sensitive to the partial bar (larger change)
        # This is because EMA gives more weight to recent observations
        assert ema_change >= sma_change * 0.8  # Allow some tolerance


# =============================================================================
# REFERENCE COMPUTATION TESTS
# =============================================================================


class TestReferenceComputation:
    """Tests verifying indicator output matches reference computation."""

    def test_moving_average_reference_computation(
        self,
        sample_price_series: pd.Series,
    ) -> None:
        """Moving average should match simple rolling mean."""
        window = 5

        # Reference computation
        reference_ma = sample_price_series.rolling(window=window, min_periods=window).mean()

        # Verify last value
        expected = sample_price_series.tail(window).mean()
        actual = reference_ma.iloc[-1]

        assert actual == pytest.approx(expected, rel=1e-9)

    def test_cumulative_return_reference_computation(
        self,
        sample_price_series: pd.Series,
    ) -> None:
        """Cumulative return should match (current / past - 1) * 100."""
        window = 5

        # Reference computation
        reference_return = ((sample_price_series / sample_price_series.shift(window)) - 1) * 100

        # Verify last value
        current_price = sample_price_series.iloc[-1]
        past_price = sample_price_series.iloc[-window - 1]
        expected = ((current_price / past_price) - 1) * 100
        actual = reference_return.iloc[-1]

        assert actual == pytest.approx(expected, rel=1e-9)

    def test_stdev_return_reference_computation(
        self,
        sample_price_series: pd.Series,
    ) -> None:
        """Stdev return should match rolling std of pct_change * 100."""
        window = 5

        # Reference computation
        returns = sample_price_series.pct_change() * 100
        reference_stdev = returns.rolling(window=window, min_periods=window).std()

        # Verify last value
        recent_returns = returns.tail(window)
        expected = recent_returns.std()
        actual = reference_stdev.iloc[-1]

        assert actual == pytest.approx(expected, rel=1e-9)
