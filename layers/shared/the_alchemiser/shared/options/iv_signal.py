"""Business Unit: shared | Status: current.

Implied Volatility (IV) signal calculator for hedge evaluation.

Replaces the VIX proxy (VIXY x 10) with proper IV data from the actual
hedge underlying (QQQ, SPY). Calculates:
- ATM IV for the target tenor (60-90 DTE)
- IV percentile over rolling 252-day window
- Skew metric (25-delta put IV - ATM IV)

This provides a more accurate measure of actual protection costs
and market volatility regime than the VIX proxy.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from ..errors.exceptions import IVDataStaleError
from ..logging import get_logger
from .adapters.iv_history_repository import (
    MIN_OBSERVATIONS_FOR_PERCENTILE,
    IVHistoryRepository,
)
from .schemas.option_contract import OptionType

if TYPE_CHECKING:
    from ..config.container import ApplicationContainer
    from .schemas.option_contract import OptionContract

logger = get_logger(__name__)


@dataclass(frozen=True)
class IVSignal:
    """Implied volatility signal metrics.

    Contains all IV-related metrics needed for regime classification
    and hedge sizing decisions.
    """

    underlying_symbol: str  # Underlying ETF (QQQ, SPY)
    atm_iv: Decimal  # ATM IV for target tenor (annualized, e.g., 0.20 = 20%)
    put_25delta_iv: Decimal  # 25-delta put IV (annualized)
    iv_skew: Decimal  # Skew: 25-delta put IV - ATM IV (positive = put skew)
    iv_percentile: Decimal  # IV percentile over 252-day window (0-100)
    timestamp: datetime  # When this signal was calculated
    target_dte: int  # Target DTE used for IV calculation (60-90 days)
    # Historical IV data for percentile calculation
    historical_iv_count: int  # Number of historical IV observations used


@dataclass(frozen=True)
class IVRegime:
    """Volatility regime classification based on IV signal.

    Replaces the VIX-based regime (low/mid/high) with IV percentile-based
    regime that directly reflects the cost of protection for the actual
    hedge underlying.
    """

    regime: str  # "low", "mid", "high"
    iv_percentile: Decimal  # IV percentile (0-100)
    iv_skew: Decimal  # Current skew metric
    skew_rich: bool  # Whether skew is rich (elevated put premium)
    reason: str  # Human-readable explanation of regime classification


# ═══════════════════════════════════════════════════════════════════════════════
# IV REGIME THRESHOLDS
# ═══════════════════════════════════════════════════════════════════════════════

# IV percentile thresholds for regime classification
# Low regime: IV is cheap (< 30th percentile) - buy protection aggressively
# Mid regime: IV is normal (30th-70th percentile) - standard hedging
# High regime: IV is expensive (> 70th percentile) - reduce hedge intensity
IV_PERCENTILE_LOW_THRESHOLD: Decimal = Decimal("30")  # < 30th percentile = low
IV_PERCENTILE_HIGH_THRESHOLD: Decimal = Decimal("70")  # > 70th percentile = high

# Skew richness threshold (in IV points)
# Positive skew is normal (puts cost more than calls due to demand)
# But when skew exceeds this threshold, put protection is "rich"
# Typical ATM IV: 15-25%, typical skew: 2-5 IV points
# Rich skew: > 8 IV points (e.g., 25-delta put at 28%, ATM at 20%)
SKEW_RICH_THRESHOLD: Decimal = Decimal("0.08")  # 8 percentage points

# Maximum age of IV data before considering it stale (seconds)
# Options data should be intraday - anything older than 1 hour is stale
MAX_IV_DATA_AGE_SECONDS: int = 3600  # 1 hour

# Target DTE range for IV calculation
# We want IV for the tenor we're actually trading (60-90 DTE)
IV_TARGET_DTE_MIN: int = 60
IV_TARGET_DTE_MAX: int = 90

# Delta targets for IV calculation
# ATM: closest to 0.50 delta
# 25-delta put: target delta of 0.25 (OTM protection)
ATM_DELTA_TARGET: Decimal = Decimal("0.50")
SKEW_DELTA_TARGET: Decimal = Decimal("0.25")

# Tolerance for delta matching (how far from target delta we'll accept)
DELTA_TOLERANCE: Decimal = Decimal("0.05")  # ±5 delta points

# Minimum number of historical IV observations required for percentile
# Need ~1 year of trading days = 252 days minimum
MIN_HISTORICAL_IV_OBSERVATIONS: int = 126  # 6 months minimum, prefer 252

# ═══════════════════════════════════════════════════════════════════════════════
# IV PERCENTILE APPROXIMATION THRESHOLDS (PLACEHOLDER)
# ═══════════════════════════════════════════════════════════════════════════════
# These thresholds map ATM IV to approximate percentile values.
# This is a placeholder until historical IV tracking is implemented in DynamoDB.
# Based on typical equity index IV ranges (QQQ, SPY).
IV_APPROX_VERY_LOW_THRESHOLD: Decimal = Decimal("15")  # IV < 15% → very low (0-10th pctl)
IV_APPROX_LOW_THRESHOLD: Decimal = Decimal("20")  # IV 15-20% → low (10th-30th pctl)
IV_APPROX_NORMAL_THRESHOLD: Decimal = Decimal("30")  # IV 20-30% → normal (30th-70th pctl)
IV_APPROX_HIGH_THRESHOLD: Decimal = Decimal("40")  # IV 30-40% → high (70th-90th pctl)
# IV > 40% → very high (90th-100th pctl)


class IVSignalCalculator:
    """Calculates IV signals from options chain data.

    Fetches option chain for the hedge underlying, identifies ATM and
    25-delta put options, extracts IV, and calculates percentile
    from historical IV data stored in DynamoDB.
    """

    def __init__(
        self,
        container: ApplicationContainer,
        iv_history_repo: IVHistoryRepository | None = None,
    ) -> None:
        """Initialize IV signal calculator.

        Args:
            container: Application DI container for accessing AlpacaOptionsAdapter
            iv_history_repo: Optional IV history repository for percentile calculation.
                            If not provided, will be created from environment variable.

        """
        self._container = container
        self._iv_history_repo = iv_history_repo

    def _get_iv_history_repo(self) -> IVHistoryRepository | None:
        """Get or create the IV history repository.

        Returns:
            IVHistoryRepository instance or None if table not configured

        """
        if self._iv_history_repo is not None:
            return self._iv_history_repo

        # Try to create from environment variable
        table_name = os.environ.get("IV_HISTORY_TABLE_NAME")
        if table_name:
            self._iv_history_repo = IVHistoryRepository(table_name)
            return self._iv_history_repo

        logger.warning("IV_HISTORY_TABLE_NAME not set, will use approximation for IV percentile")
        return None

    def calculate_iv_signal(
        self,
        underlying_symbol: str,
        underlying_price: Decimal,
        correlation_id: str | None = None,
    ) -> IVSignal:
        """Calculate IV signal for the underlying.

        Args:
            underlying_symbol: Underlying ETF symbol (QQQ, SPY)
            underlying_price: Current price of underlying
            correlation_id: Optional correlation ID for tracing

        Returns:
            IVSignal with ATM IV, skew, and percentile

        Raises:
            IVDataStaleError: If IV data is unavailable or too old

        """
        logger.info(
            "Calculating IV signal",
            underlying_symbol=underlying_symbol,
            underlying_price=str(underlying_price),
            correlation_id=correlation_id,
        )

        try:
            # Get options adapter
            alpaca_options = self._container.infrastructure.alpaca_options_adapter()

            # Calculate target expiration date range (60-90 DTE from today)
            today = datetime.now(UTC).date()
            min_expiry = today + timedelta(days=IV_TARGET_DTE_MIN)
            max_expiry = today + timedelta(days=IV_TARGET_DTE_MAX)

            # Fetch option chain for puts in target DTE range
            # We need both ATM and OTM puts for skew calculation
            option_chain = alpaca_options.get_option_chain(
                underlying_symbol=underlying_symbol,
                expiration_date_gte=min_expiry,
                expiration_date_lte=max_expiry,
                option_type=OptionType.PUT,
                limit=100,
            )

            if not option_chain:
                raise IVDataStaleError(
                    message=f"No option chain data available for {underlying_symbol}",
                    underlying_symbol=underlying_symbol,
                    correlation_id=correlation_id,
                )

            # Filter options with valid IV data
            valid_options = [
                opt
                for opt in option_chain
                if opt.implied_volatility is not None
                and opt.delta is not None
                and opt.bid_price is not None
                and opt.ask_price is not None
                and opt.open_interest > 0
            ]

            if not valid_options:
                raise IVDataStaleError(
                    message=f"No options with valid IV data for {underlying_symbol}",
                    underlying_symbol=underlying_symbol,
                    correlation_id=correlation_id,
                )

            # Find ATM option (closest to 0.50 delta)
            atm_option = self._find_atm_option(valid_options, underlying_price)
            if atm_option is None or atm_option.implied_volatility is None:
                raise IVDataStaleError(
                    message=f"Could not find ATM option with IV for {underlying_symbol}",
                    underlying_symbol=underlying_symbol,
                    correlation_id=correlation_id,
                )

            atm_iv = atm_option.implied_volatility

            # Find 25-delta put for skew
            put_25delta = self._find_delta_target_put(valid_options, SKEW_DELTA_TARGET)
            if put_25delta is None or put_25delta.implied_volatility is None:
                # Fallback: estimate skew from strike spread if exact delta not available
                logger.warning(
                    "Could not find 25-delta put, using ATM IV only",
                    underlying_symbol=underlying_symbol,
                    correlation_id=correlation_id,
                )
                put_25delta_iv = atm_iv  # Conservative fallback
                iv_skew = Decimal("0")  # No skew if we can't measure it
            else:
                put_25delta_iv = put_25delta.implied_volatility
                iv_skew = put_25delta_iv - atm_iv

            # Calculate IV percentile from historical data
            iv_percentile, historical_count = self._calculate_iv_percentile(
                underlying_symbol=underlying_symbol,
                current_iv=atm_iv,
                put_25delta_iv=put_25delta_iv,
                target_dte=(IV_TARGET_DTE_MIN + IV_TARGET_DTE_MAX) // 2,
            )

            # Calculate average DTE of options used
            avg_dte = sum(opt.days_to_expiry for opt in [atm_option, put_25delta] if opt) // max(
                1, sum(1 for opt in [atm_option, put_25delta] if opt)
            )

            signal = IVSignal(
                underlying_symbol=underlying_symbol,
                atm_iv=atm_iv,
                put_25delta_iv=put_25delta_iv,
                iv_skew=iv_skew,
                iv_percentile=iv_percentile,
                timestamp=datetime.now(UTC),
                target_dte=avg_dte,
                historical_iv_count=historical_count,
            )

            logger.info(
                "IV signal calculated",
                underlying_symbol=underlying_symbol,
                atm_iv=str(atm_iv),
                put_25delta_iv=str(put_25delta_iv),
                iv_skew=str(iv_skew),
                iv_percentile=str(iv_percentile),
                correlation_id=correlation_id,
            )

            return signal

        except IVDataStaleError:
            # Re-raise fail-closed errors
            raise
        except Exception as e:
            # Any other error is also a fail-closed condition
            logger.error(
                "Failed to calculate IV signal - FAILING CLOSED",
                underlying_symbol=underlying_symbol,
                error=str(e),
                exc_info=True,
                correlation_id=correlation_id,
                fail_closed_condition="iv_calculation_failed",
                alert_required=True,
            )
            raise IVDataStaleError(
                message=f"Failed to calculate IV signal for {underlying_symbol}: {e!s}",
                underlying_symbol=underlying_symbol,
                correlation_id=correlation_id,
            ) from e

    def _find_atm_option(
        self,
        options: list[OptionContract],
        underlying_price: Decimal,
    ) -> OptionContract | None:
        """Find the ATM option (closest to 0.50 delta).

        Args:
            options: List of option contracts with valid delta
            underlying_price: Current underlying price

        Returns:
            ATM option or None if not found

        """
        # Find option with delta closest to ATM_DELTA_TARGET (0.50 for puts)
        # For puts, delta is negative, so we want closest to -0.50
        target_delta = -ATM_DELTA_TARGET  # -0.50 for puts

        atm_candidate = None
        min_delta_diff = Decimal("1.0")  # Start with max possible difference

        for opt in options:
            if opt.delta is None:
                continue

            delta_diff = abs(opt.delta - target_delta)
            if delta_diff < min_delta_diff and delta_diff <= DELTA_TOLERANCE:
                min_delta_diff = delta_diff
                atm_candidate = opt

        if atm_candidate is None:
            logger.warning(
                "Could not find ATM option within tolerance",
                target_delta=str(target_delta),
                tolerance=str(DELTA_TOLERANCE),
            )

        return atm_candidate

    def _find_delta_target_put(
        self,
        options: list[OptionContract],
        target_delta: Decimal,
    ) -> OptionContract | None:
        """Find put option closest to target delta.

        Args:
            options: List of option contracts with valid delta
            target_delta: Target delta (e.g., 0.25 for 25-delta put)

        Returns:
            Option closest to target delta or None

        """
        # For puts, delta is negative
        target_delta_signed = -target_delta

        candidate = None
        min_delta_diff = Decimal("1.0")

        for opt in options:
            if opt.delta is None:
                continue

            delta_diff = abs(opt.delta - target_delta_signed)
            if delta_diff < min_delta_diff and delta_diff <= DELTA_TOLERANCE:
                min_delta_diff = delta_diff
                candidate = opt

        if candidate is None:
            logger.warning(
                "Could not find put option at target delta",
                target_delta=str(target_delta),
                tolerance=str(DELTA_TOLERANCE),
            )

        return candidate

    def _calculate_iv_percentile(
        self,
        underlying_symbol: str,
        current_iv: Decimal,
        put_25delta_iv: Decimal,
        target_dte: int,
    ) -> tuple[Decimal, int]:
        """Calculate IV percentile over rolling 252-day window.

        Uses historical IV data from DynamoDB when available. Falls back to
        approximation when insufficient historical data exists (<126 observations).

        Also records the current IV observation to build history over time.

        Args:
            underlying_symbol: Underlying symbol
            current_iv: Current ATM IV
            put_25delta_iv: Current 25-delta put IV
            target_dte: Target DTE for IV calculation

        Returns:
            Tuple of (IV percentile 0-100, observation count used)

        """
        iv_history_repo = self._get_iv_history_repo()

        # Record current IV observation (idempotent by date)
        if iv_history_repo is not None:
            iv_history_repo.record_daily_iv(
                underlying_symbol=underlying_symbol,
                atm_iv=current_iv,
                put_25delta_iv=put_25delta_iv,
                dte_used=target_dte,
            )

        # Try to calculate percentile from historical data
        if iv_history_repo is not None:
            percentile, observation_count = iv_history_repo.calculate_percentile(
                underlying_symbol=underlying_symbol,
                current_iv=current_iv,
            )

            # Check if we have sufficient history
            if observation_count >= MIN_OBSERVATIONS_FOR_PERCENTILE:
                logger.info(
                    "Calculated IV percentile from historical data",
                    underlying_symbol=underlying_symbol,
                    current_iv=str(current_iv),
                    percentile=str(percentile),
                    observation_count=observation_count,
                    method="historical",
                )
                return percentile, observation_count

            # Insufficient history - fall back to approximation with warning
            logger.warning(
                "Insufficient IV history for accurate percentile - using approximation",
                underlying_symbol=underlying_symbol,
                observation_count=observation_count,
                min_required=MIN_OBSERVATIONS_FOR_PERCENTILE,
                note="Percentile accuracy will improve as more daily observations accumulate",
            )

        # Fallback: Map IV to approximate percentile using static thresholds
        percentile = self._approximate_iv_percentile(current_iv, underlying_symbol)
        return percentile, 0  # 0 indicates approximation used

    def _approximate_iv_percentile(
        self,
        current_iv: Decimal,
        underlying_symbol: str,
    ) -> Decimal:
        """Approximate IV percentile using static thresholds.

        This is the fallback method when historical data is unavailable.
        Based on typical equity index IV ranges (QQQ, SPY).

        Args:
            current_iv: Current ATM IV
            underlying_symbol: Underlying symbol (for logging)

        Returns:
            Approximate IV percentile (0-100)

        """
        iv_pct = float(current_iv * 100)  # Convert to percentage (0.20 → 20)

        very_low = float(IV_APPROX_VERY_LOW_THRESHOLD)
        low = float(IV_APPROX_LOW_THRESHOLD)
        normal = float(IV_APPROX_NORMAL_THRESHOLD)
        high = float(IV_APPROX_HIGH_THRESHOLD)

        if iv_pct < very_low:
            # Very low IV → 0-10th percentile
            percentile = (iv_pct / very_low) * 10
        elif iv_pct < low:
            # Low IV → 10th-30th percentile
            percentile = 10 + ((iv_pct - very_low) / (low - very_low)) * 20
        elif iv_pct < normal:
            # Normal IV → 30th-70th percentile
            percentile = 30 + ((iv_pct - low) / (normal - low)) * 40
        elif iv_pct < high:
            # High IV → 70th-90th percentile
            percentile = 70 + ((iv_pct - normal) / (high - normal)) * 20
        else:
            # Very high IV → 90th-100th percentile
            percentile = 90 + min(((iv_pct - high) / 20) * 10, 10)

        logger.info(
            "IV percentile approximation (fallback method)",
            underlying_symbol=underlying_symbol,
            current_iv=str(current_iv),
            iv_pct=str(iv_pct),
            percentile=str(percentile),
            method="approximation",
            note="Using static thresholds - historical data not yet available",
        )

        return Decimal(str(percentile))


def classify_iv_regime(signal: IVSignal) -> IVRegime:
    """Classify volatility regime based on IV signal.

    Args:
        signal: IV signal with percentile and skew

    Returns:
        IVRegime classification

    """
    # Determine base regime from IV percentile
    if signal.iv_percentile < IV_PERCENTILE_LOW_THRESHOLD:
        base_regime = "low"
        regime_reason = (
            f"IV at {signal.iv_percentile:.1f}th percentile (< {IV_PERCENTILE_LOW_THRESHOLD})"
        )
    elif signal.iv_percentile < IV_PERCENTILE_HIGH_THRESHOLD:
        base_regime = "mid"
        regime_reason = f"IV at {signal.iv_percentile:.1f}th percentile ({IV_PERCENTILE_LOW_THRESHOLD}-{IV_PERCENTILE_HIGH_THRESHOLD})"
    else:
        base_regime = "high"
        regime_reason = (
            f"IV at {signal.iv_percentile:.1f}th percentile (> {IV_PERCENTILE_HIGH_THRESHOLD})"
        )

    # Check if skew is rich (elevated put premium)
    skew_rich = signal.iv_skew > SKEW_RICH_THRESHOLD

    if skew_rich:
        regime_reason += f"; Skew rich ({signal.iv_skew:.1%} > {SKEW_RICH_THRESHOLD:.1%})"

    return IVRegime(
        regime=base_regime,
        iv_percentile=signal.iv_percentile,
        iv_skew=signal.iv_skew,
        skew_rich=skew_rich,
        reason=regime_reason,
    )
