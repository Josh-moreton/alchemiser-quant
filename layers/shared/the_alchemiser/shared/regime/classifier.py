"""Business Unit: shared | Status: current.

HMM-based market regime classifier service.

This module extracts the core HMM classification logic from hmm.py into a
production-ready service that can be called from the regime detector Lambda.
Uses a 2-state Hidden Markov Model to classify market regimes based on SPY features.

Key Features:
- 2-state HMM model (bullish/bearish base states)
- Probability-based regime classification into 5 types
- Configurable persistence for regime transitions
- Returns frozen RegimeState DTO for caching in DynamoDB

Note: This module requires optional dependencies (hmmlearn, pandas, numpy)
that are only available in the regime detector Lambda layer.
"""

from __future__ import annotations

import warnings
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from hmmlearn import hmm

from .schemas import RegimeState, RegimeType

if TYPE_CHECKING:
    from numpy.typing import NDArray

# Suppress convergence warnings from hmmlearn
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


class HMMRegimeClassifier:
    """HMM-based market regime classifier using SPY features.

    Uses a 2-state Gaussian HMM to identify base bullish/bearish states,
    then classifies into 5 probability-based regimes:
    - Risk-On: >60% probability in bullish state
    - Risk-Off: >60% probability in bearish state
    - Recovery: Risk-Off but with positive recent returns
    - Pivot+: 40-60% range transitioning from Risk-Off to Risk-On
    - Pivot-: 40-60% range transitioning from Risk-On to Risk-Off
    """

    # Probability thresholds for regime classification
    BULLISH_THRESHOLD = 0.60  # Above this = Risk-On
    BEARISH_THRESHOLD = 0.40  # Below this = Risk-Off/Recovery

    # Lookback periods for features
    VOL_WINDOW = 20
    MOMENTUM_WINDOW = 20
    MOMENTUM_LT_WINDOW = 50
    RANGE_VOL_WINDOW = 10

    # HMM fitting parameters
    N_TRIALS = 5  # Number of random restarts
    N_ITER = 1000  # Max EM iterations

    def __init__(self, min_regime_duration: int = 10, use_recovery: bool = True) -> None:
        """Initialize the HMM classifier.

        Args:
            min_regime_duration: Minimum days to confirm a regime change
            use_recovery: Whether to classify Recovery as separate from Risk-Off

        """
        self.min_regime_duration = min_regime_duration
        self.use_recovery = use_recovery
        self._model: hmm.GaussianHMM | None = None
        self._feature_means: NDArray[np.float64] | None = None
        self._feature_stds: NDArray[np.float64] | None = None
        self._bullish_state: int = 0
        self._state_probabilities: NDArray[np.float64] | None = None

    def prepare_features(self, spy_data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for HMM from SPY OHLC data.

        Features based on QuantConnect + academic research:
        - daily_range: (High-Low)/Close (intraday volatility)
        - drawdown: Running drawdown from peak (downside risk)
        - momentum_LT: 50-day return (long-term trend)
        - momentum: 20-day return (short-term trend)

        Args:
            spy_data: DataFrame with SPY OHLC price data (columns: Open, High, Low, Close)

        Returns:
            DataFrame with computed features and SPY_Close for reference

        Raises:
            ValueError: If required columns are missing or data is insufficient

        """
        required_cols = {"Open", "High", "Low", "Close"}
        if isinstance(spy_data.columns, pd.MultiIndex):
            # Handle multi-level columns from yfinance
            available_cols = set(spy_data.columns.get_level_values(0))
        else:
            available_cols = set(spy_data.columns)

        missing = required_cols - available_cols
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df = pd.DataFrame(index=spy_data.index)

        # Extract prices - handle both single and multi-level columns
        if isinstance(spy_data.columns, pd.MultiIndex):
            spy_close = spy_data["Close"].iloc[:, 0]
            spy_high = spy_data["High"].iloc[:, 0]
            spy_low = spy_data["Low"].iloc[:, 0]
        else:
            spy_close = (
                spy_data["Close"]
                if isinstance(spy_data["Close"], pd.Series)
                else spy_data["Close"].squeeze()
            )
            spy_high = (
                spy_data["High"]
                if isinstance(spy_data["High"], pd.Series)
                else spy_data["High"].squeeze()
            )
            spy_low = (
                spy_data["Low"]
                if isinstance(spy_data["Low"], pd.Series)
                else spy_data["Low"].squeeze()
            )

        # Calculate log returns
        df["SPY_log_returns"] = np.log(spy_close / spy_close.shift(1))

        # Feature 1: Daily range (intraday volatility)
        df["daily_range"] = (spy_high - spy_low) / spy_close

        # Feature 2: Drawdown from peak
        cumulative = (1 + df["SPY_log_returns"]).cumprod()
        running_max = cumulative.expanding().max()
        df["drawdown"] = (cumulative - running_max) / running_max

        # Feature 3: Long-term momentum (50-day)
        df["momentum_LT"] = spy_close.pct_change(self.MOMENTUM_LT_WINDOW)

        # Feature 4: Short-term momentum (20-day)
        df["momentum"] = spy_close.pct_change(self.MOMENTUM_WINDOW)

        # Store SPY close for reference
        df["SPY_Close"] = spy_close.values

        # Drop NaN rows
        df = df.dropna()

        if len(df) < self.MOMENTUM_LT_WINDOW + 10:
            raise ValueError(
                f"Insufficient data: need at least {self.MOMENTUM_LT_WINDOW + 10} days, "
                f"got {len(df)}"
            )

        return df

    def fit(self, features_df: pd.DataFrame) -> None:
        """Fit the 2-state HMM model to features.

        Args:
            features_df: DataFrame with features from prepare_features()

        Raises:
            RuntimeError: If HMM fitting fails after all trials

        """
        feature_cols = ["daily_range", "drawdown", "momentum_LT", "momentum"]
        X = features_df[feature_cols].values

        # Standardize features
        self._feature_means = np.mean(X, axis=0)
        self._feature_stds = np.std(X, axis=0)
        X_scaled = (X - self._feature_means) / self._feature_stds

        # Fit 2-state HMM with multiple random restarts
        best_model: hmm.GaussianHMM | None = None
        best_score = -np.inf

        for trial in range(self.N_TRIALS):
            try:
                model = hmm.GaussianHMM(
                    n_components=2,
                    covariance_type="full",
                    n_iter=self.N_ITER,
                    random_state=42 + trial,
                )
                model.fit(X_scaled)
                score = model.score(X_scaled)

                if score > best_score:
                    best_score = score
                    best_model = model

            except Exception:
                # Trial failed, continue to next
                continue

        if best_model is None:
            raise RuntimeError("Failed to fit HMM model after all trials")

        self._model = best_model

        # Get state predictions to identify bullish vs bearish states
        hidden_states = self._model.predict(X_scaled)
        self._state_probabilities = self._model.predict_proba(X_scaled)

        # Identify which state is bullish based on mean returns
        state_0_return = features_df.loc[hidden_states == 0, "SPY_log_returns"].mean()
        state_1_return = features_df.loc[hidden_states == 1, "SPY_log_returns"].mean()
        self._bullish_state = 0 if state_0_return > state_1_return else 1

    def classify_current_regime(self, features_df: pd.DataFrame) -> RegimeState:
        """Classify the current market regime based on latest data.

        Args:
            features_df: DataFrame with features from prepare_features()

        Returns:
            RegimeState DTO with current regime and probability

        Raises:
            ValueError: If model has not been fitted

        """
        if self._model is None:
            raise ValueError("Model not fitted. Call fit() first.")

        feature_cols = ["daily_range", "drawdown", "momentum_LT", "momentum"]
        X = features_df[feature_cols].values

        # Standardize using fitted parameters
        X_scaled = (X - self._feature_means) / self._feature_stds

        # Get probabilities for the most recent observation
        state_probs = self._model.predict_proba(X_scaled)
        latest_probs = state_probs[-1]
        bull_prob = float(latest_probs[self._bullish_state])

        # Recent returns for Recovery detection
        recent_returns = features_df["SPY_log_returns"].iloc[-20:].mean()

        # Classify regime based on probability
        regime: RegimeType
        if bull_prob > self.BULLISH_THRESHOLD:
            regime = RegimeType.RISK_ON
        elif bull_prob < self.BEARISH_THRESHOLD:
            if self.use_recovery and recent_returns > 0:
                regime = RegimeType.RECOVERY
            else:
                regime = RegimeType.RISK_OFF
        else:
            # In transition zone (40-60%)
            # Look at trend direction from previous regime
            if len(state_probs) > 5:
                prev_bull_prob = float(state_probs[-5, self._bullish_state])
                if bull_prob > prev_bull_prob:
                    regime = RegimeType.PIVOT_PLUS
                else:
                    regime = RegimeType.PIVOT_MINUS
            else:
                # Default to Pivot+ if uncertain
                regime = RegimeType.PIVOT_PLUS

        # Calculate confidence (how far from 50%)
        confidence = abs(bull_prob - 0.5) * 2  # Maps 0.5-1.0 to 0.0-1.0

        # Get model score
        model_score = float(self._model.score(X_scaled))

        return RegimeState(
            regime=regime,
            probability=Decimal(str(round(confidence, 4))),
            bull_probability=Decimal(str(round(bull_prob, 4))),
            timestamp=datetime.now(UTC),
            spy_close=Decimal(str(round(float(features_df["SPY_Close"].iloc[-1]), 2))),
            lookback_days=len(features_df),
            model_score=Decimal(str(round(model_score, 2))),
        )

    def classify_with_smoothing(self, features_df: pd.DataFrame) -> RegimeState:
        """Classify regime with smoothing to avoid rapid transitions.

        Applies minimum regime duration smoothing and returns the current
        smoothed regime. This is more stable for production use.

        Args:
            features_df: DataFrame with features from prepare_features()

        Returns:
            RegimeState with smoothed regime classification

        """
        if self._model is None:
            raise ValueError("Model not fitted. Call fit() first.")

        # Get raw classification first
        raw_state = self.classify_current_regime(features_df)

        # For smoothing, we need the full history of classifications
        feature_cols = ["daily_range", "drawdown", "momentum_LT", "momentum"]
        X = features_df[feature_cols].values
        X_scaled = (X - self._feature_means) / self._feature_stds

        state_probs = self._model.predict_proba(X_scaled)

        # Classify each day
        regimes: list[RegimeType] = []
        prev_regime: RegimeType | None = None

        for i in range(len(state_probs)):
            bull_prob = float(state_probs[i, self._bullish_state])
            recent_ret = float(features_df["SPY_log_returns"].iloc[max(0, i - 20) : i + 1].mean())

            if bull_prob > self.BULLISH_THRESHOLD:
                regime = RegimeType.RISK_ON
            elif bull_prob < self.BEARISH_THRESHOLD:
                if self.use_recovery and recent_ret > 0:
                    regime = RegimeType.RECOVERY
                else:
                    regime = RegimeType.RISK_OFF
            else:
                if prev_regime in [RegimeType.RISK_ON, RegimeType.PIVOT_PLUS]:
                    regime = RegimeType.PIVOT_MINUS
                else:
                    regime = RegimeType.PIVOT_PLUS

            regimes.append(regime)
            if regime in [RegimeType.RISK_ON, RegimeType.RISK_OFF, RegimeType.RECOVERY]:
                prev_regime = regime

        # Apply smoothing
        smoothed = self._smooth_regimes(regimes)

        # Return state with smoothed regime
        return RegimeState(
            regime=smoothed[-1],
            probability=raw_state.probability,
            bull_probability=raw_state.bull_probability,
            timestamp=raw_state.timestamp,
            spy_close=raw_state.spy_close,
            lookback_days=raw_state.lookback_days,
            model_score=raw_state.model_score,
        )

    def _smooth_regimes(self, regimes: list[RegimeType]) -> list[RegimeType]:
        """Smooth regime predictions by requiring minimum duration.

        Args:
            regimes: List of regime classifications

        Returns:
            Smoothed list where short regimes are merged with previous

        """
        if len(regimes) < self.min_regime_duration:
            return regimes

        smoothed = list(regimes)
        i = 0

        while i < len(smoothed):
            current = smoothed[i]

            # Find duration of current regime
            j = i
            while j < len(smoothed) and smoothed[j] == current:
                j += 1

            duration = j - i

            # If too short and not at start, merge with previous
            if duration < self.min_regime_duration and i > 0:
                prev = smoothed[i - 1]
                for k in range(i, j):
                    smoothed[k] = prev

            i = j

        return smoothed
