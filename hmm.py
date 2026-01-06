#!/usr/bin/env python
"""HMM-Based Market Regime Classifier.

Uses Hidden Markov Models to identify market regimes based on SPY features.

Key Features:
- 2-state HMM model (Risk-On / Risk-Off base states)
- optional recovery state added 01/02/26
- Probability-based regime classification:
  - Risk-On: >60% probability in bullish state
  - Risk-Off: >60% probability in bearish state
  - Pivot+: 40-60% range transitioning from Risk-Off to Risk-On
  - Pivot-: 40-60% range transitioning from Risk-On to Risk-Off
- Configurable persistence for regime transitions

WE WILL USE THIS to build our own market regime indicator that can weight our portfolio of strategies (currently fixed by strategy.prod.json) based on the current regime.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from hmmlearn import hmm
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

def download_data(start_date='2000-01-01', end_date=None):
    """
    Download SPY data from Yahoo Finance.

    Args:
        start_date: Start date for data download
        end_date: End date for data download (default: today)

    Returns:
        SPY data DataFrame
    """
    import yfinance as yf

    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"Downloading SPY data from {start_date} to {end_date}...")
    spy_data = yf.download('SPY', start=start_date, end=end_date, progress=False)

    print(f"Downloaded {len(spy_data)} days of data")

    return spy_data


class HMMRegimeClassifier:
    """HMM-based market regime classifier using SPY features."""

    def __init__(self, n_regimes=2):
        """Initialize the HMM classifier with 2 states (Risk-On/Risk-Off)."""
        self.n_regimes = n_regimes
        self.model = None
        self.regime_stats = None
        self.regime_names = None

        # Define colors for regimes
        self.regime_colors = {
            'Risk-On': '#90EE90',  # Light green
            'Risk-Off': '#FFB6C6',  # Light pink
            'Recovery': '#B0E0E6',  # Powder blue (Risk-Off but improving)
            'Pivot+': '#FFFACD',  # Light yellow (transitioning to Risk-On)
            'Pivot-': '#FFE4B5'  # Moccasin (transitioning to Risk-Off)
        }

    def prepare_features(self, spy_data, use_multivariate=True):
        """
        Prepare features for HMM combining research best practices.

        Features based on QuantConnect + academic research:
        - returns: Log returns (direction)
        - realized_vol: 20-day volatility (risk level)
        - momentum: 10-day return (trend strength)
        - drawdown: Running drawdown from peak (downside risk)
        - daily_range: (High-Low)/Close (intraday volatility)
        - range_vol: 10-day average range (volatility regime)

        Args:
            spy_data: DataFrame with SPY OHLC price data
            use_multivariate: Use multiple features (True) or just returns (False)

        Returns:
            DataFrame with features and metadata
        """
        df = pd.DataFrame(index=spy_data.index)

        # Extract prices - handle both single and multi-level columns
        if isinstance(spy_data.columns, pd.MultiIndex):
            spy_close = spy_data['Close'].iloc[:, 0]
            spy_high = spy_data['High'].iloc[:, 0]
            spy_low = spy_data['Low'].iloc[:, 0]
        else:
            spy_close = spy_data['Close'] if isinstance(spy_data['Close'], pd.Series) else spy_data['Close'].squeeze()
            spy_high = spy_data['High'] if isinstance(spy_data['High'], pd.Series) else spy_data['High'].squeeze()
            spy_low = spy_data['Low'] if isinstance(spy_data['Low'], pd.Series) else spy_data['Low'].squeeze()

        # Calculate SPY log returns
        df['SPY_log_returns'] = np.log(spy_close / spy_close.shift(1))

        if use_multivariate:
            # Feature 1: Raw log returns (captures direction)
            df['returns'] = df['SPY_log_returns']

            # Feature 2: 20-day realized volatility (captures turbulence)
            df['realized_vol'] = df['SPY_log_returns'].rolling(window=20).std()

            # Feature 3: Momentum - 20-day and 50-day
            df['momentum'] = spy_close.pct_change(20)
            df['momentum_LT'] = spy_close.pct_change(50)

            # Feature 4: DRAWDOWN (QuantConnect approach for downside risk detection)
            cumulative = (1 + df['SPY_log_returns']).cumprod()
            running_max = cumulative.expanding().max()
            df['drawdown'] = (cumulative - running_max) / running_max

            # Feature 5: DAILY RANGE (QuantConnect approach for intraday volatility)
            df['daily_range'] = (spy_high - spy_low) / spy_close

            # Feature 6: RANGE VOLATILITY (10-day average range)
            df['range_vol'] = df['daily_range'].rolling(window=10).mean()

            print(f"\nMultivariate features prepared:")
            print(f"  Returns: mean={df['returns'].mean() * 100:.4f}%, std={df['returns'].std() * 100:.4f}%")
            print(
                f"  Realized Vol (20d): mean={df['realized_vol'].mean() * 100:.4f}%, std={df['realized_vol'].std() * 100:.4f}%")
            print(f"  Momentum (20d): mean={df['momentum'].mean() * 100:.4f}%, std={df['momentum'].std() * 100:.4f}%")
            print(f"  Drawdown: mean={df['drawdown'].mean() * 100:.4f}%, std={df['drawdown'].std() * 100:.4f}%")
            print(
                f"  Daily Range: mean={df['daily_range'].mean() * 100:.4f}%, std={df['daily_range'].std() * 100:.4f}%")
            print(
                f"  Range Vol (10d): mean={df['range_vol'].mean() * 100:.4f}%, std={df['range_vol'].std() * 100:.4f}%")
        else:
            # Simple: just returns
            df['returns'] = df['SPY_log_returns']
            print(f"\nSingle feature prepared:")
            print(f"  Returns: mean={df['returns'].mean() * 100:.4f}%, std={df['returns'].std() * 100:.4f}%")

        # Store raw data for visualization
        df['SPY_Close'] = spy_close.values

        df = df.dropna()

        return df

    def fit_and_classify(self, features_df, use_multivariate=True, min_regime_duration=5, use_recovery=True):
        """
        Fit 2-state HMM model and classify regimes with probability-based states.

        The 2-state HMM provides base states, then we classify into 4-5 regimes:
        - Risk-On: >60% probability in bullish state
        - Risk-Off: >60% probability in bearish state (with negative returns)
        - Recovery: >60% probability in bearish state BUT positive returns (optional)
        - Pivot+: 40-60% range, transitioning from Risk-Off to Risk-On
        - Pivot-: 40-60% range, transitioning from Risk-On to Risk-Off

        Args:
            features_df: DataFrame with features
            use_multivariate: Use multiple features or single feature
            min_regime_duration: Minimum number of days to stay in a regime (smoothing filter)
            use_recovery: If True, sub-classify Risk-Off into Recovery vs pure Risk-Off (default: True)

        Returns:
            Series with regime classifications
        """
        if use_multivariate:
            feature_cols = ['daily_range', 'drawdown', 'momentum_LT', 'momentum']#, 'returns','range_vol','momentum_ST']
        else:
            feature_cols = ['returns']

        X = features_df[feature_cols].values

        # Standardize features for HMM
        self.feature_means = np.mean(X, axis=0)
        self.feature_stds = np.std(X, axis=0)
        X_scaled = (X - self.feature_means) / self.feature_stds

        print(f"\nFeature standardization:")
        for i, col in enumerate(feature_cols):
            print(f"  {col}: mean={self.feature_means[i]:.6f}, std={self.feature_stds[i]:.6f}")

        # Always use 2-state model
        print(f"\nFitting 2-state HMM model...")
        self.n_regimes = 2

        best_model = None
        best_score = -np.inf

        for trial in range(5):
            try:
                model = hmm.GaussianHMM(
                    n_components=2,
                    covariance_type="full",
                    n_iter=1000,
                    random_state=42 + trial
                )
                model.fit(X_scaled)
                score = model.score(X_scaled)

                if score > best_score:
                    best_score = score
                    best_model = model

            except Exception as e:
                print(f"Trial {trial + 1} failed: {e}")
                continue

        if best_model is None:
            raise RuntimeError(f"Failed to fit 2-state model")

        self.model = best_model
        print(f"Fitted 2-state model: LL={best_score:.2f}, BIC={best_model.bic(X_scaled):.2f}")

        # Get base state predictions and probabilities
        hidden_states = self.model.predict(X_scaled)
        self.state_probabilities = self.model.predict_proba(X_scaled)

        # Characterize base states (Risk-On vs Risk-Off)
        self._characterize_base_states(features_df, hidden_states)

        # Identify which state is bullish (Risk-On) vs bearish (Risk-Off)
        state_0_return = features_df.loc[hidden_states == 0, 'SPY_log_returns'].mean()
        state_1_return = features_df.loc[hidden_states == 1, 'SPY_log_returns'].mean()

        bullish_state = 0 if state_0_return > state_1_return else 1
        bearish_state = 1 - bullish_state

        print(f"\nBase state identification:")
        print(
            f"  State {bullish_state}: Risk-On (mean return: {state_0_return if bullish_state == 0 else state_1_return:.4%})")
        print(
            f"  State {bearish_state}: Risk-Off (mean return: {state_1_return if bullish_state == 0 else state_0_return:.4%})")

        # Create 5-regime classification based on probabilities and returns
        regime_labels = []
        prev_regime = None

        # Debug: Track probability progression for analysis
        debug_log = []

        for i in range(len(self.state_probabilities)):
            bull_prob = self.state_probabilities[i, bullish_state]
            # Look at recent returns to detect recovery periods
            lookback = min(20, i)  # Use up to 20 days or whatever is available
            recent_returns = features_df.iloc[max(0, i - lookback):i + 1]['SPY_log_returns'].mean()

            if bull_prob > 0.6:
                regime = 'Risk-On'
            elif bull_prob < 0.4:
                # Risk-Off, but optionally check if returns are improving
                if use_recovery:
                    if lookback > 0:
                        # If average daily return is positive despite Risk-Off classification
                        if recent_returns > 0.0005:  # ~0.13% annualized threshold
                            regime = 'Risk-On'  # High vol/uncertainty but positive returns
                        else:
                            regime = 'Risk-Off'
                    else:
                        regime = 'Risk-Off'
                else:
                    # Simple 2-state: just Risk-Off
                    regime = 'Risk-Off'
            else:
                # In transition zone (40-60%)
                # Determine direction based on previous confirmed regime
                if prev_regime in ['Risk-On', 'Pivot+']:
                    regime = 'Pivot-'  # Transitioning away from Risk-On
                else:
                    regime = 'Pivot+'  # Transitioning toward Risk-On

            regime_labels.append(regime)

            # Debug logging for probability analysis
            if i > 0 and regime != regime_labels[i - 1]:
                debug_log.append({
                    'date': features_df.index[i],
                    'regime': regime,
                    'prev_regime': regime_labels[i - 1],
                    'bull_prob': bull_prob,
                    'index': i
                })

            # Update previous regime (only for confirmed states, not pivots)
            if regime in ['Risk-On', 'Risk-Off', 'Recovery']:
                prev_regime = regime

        # Store debug log for later analysis
        self.probability_debug_log = debug_log

        regime_array = np.array(regime_labels)

        # Apply minimum regime duration smoothing
        if min_regime_duration > 1:
            regime_array = self._smooth_regimes(regime_array, min_duration=min_regime_duration)
            print(f"Applied {min_regime_duration}-day minimum regime duration smoothing")

        # Store regime names for the 4 states
        self.regime_names = {
            'Risk-On': 'Risk-On',
            'Risk-Off': 'Risk-Off',
            'Pivot+': 'Pivot+',
            'Pivot-': 'Pivot-'
        }

        # Calculate regime statistics
        self._calculate_regime_statistics(features_df, regime_array)

        # Create regime series
        regime_series = pd.Series(regime_array, index=features_df.index)

        return regime_series

    def detect_regime_transitions_by_probability(self, regimes, probability_threshold=0.90,
                                                 lookback_days=5):
        """
        Detect regime transitions using HMM state probabilities instead of fixed duration.

        A transition is signaled when:
        1. The regime has changed from the previous confirmed regime
        2. The model's confidence (max probability) exceeds the threshold
        3. The average probability over lookback_days exceeds the threshold

        Args:
            regimes: Series with regime classifications
            probability_threshold: Minimum probability to confirm state (default: 0.80)
            lookback_days: Days to average probability over (default: 5)

        Returns:
            List of dictionaries with transition information including probabilities
        """
        if not hasattr(self, 'state_probabilities'):
            print("Warning: State probabilities not available, falling back to duration-based detection")
            return self.detect_regime_transitions(regimes, min_duration=10)

        if len(regimes) < lookback_days:
            return []

        transitions = []

        # Map regime names back to state indices
        regime_to_state = {name: state for state, name in self.regime_names.items()}
        state_sequence = np.array([regime_to_state[r] for r in regimes.values])

        confirmed_regime = regimes.iloc[0]
        confirmed_state = state_sequence[0]
        last_transition_idx = 0

        for i in range(lookback_days, len(regimes)):
            current_regime = regimes.iloc[i]
            current_state = state_sequence[i]

            # Check if regime has changed from confirmed regime
            if current_regime != confirmed_regime:
                # Get current probability for the new state
                current_prob = self.state_probabilities[i, current_state]

                # Get average probability over lookback period
                lookback_probs = self.state_probabilities[i - lookback_days + 1:i + 1, current_state]
                avg_prob = np.mean(lookback_probs)

                # Check if both current and average probabilities exceed threshold
                if current_prob >= probability_threshold and avg_prob >= probability_threshold:
                    # Transition confirmed!
                    duration_in_old = i - last_transition_idx

                    transitions.append({
                        'date': regimes.index[i],
                        'transition_start_date': regimes.index[i],  # More immediate with probability
                        'from_regime': confirmed_regime,
                        'to_regime': current_regime,
                        'duration_in_old': duration_in_old,
                        'transition_start_idx': i,
                        'confirmation_idx': i,
                        'current_probability': current_prob,
                        'avg_probability': avg_prob,
                        'probability_threshold': probability_threshold
                    })

                    confirmed_regime = current_regime
                    confirmed_state = current_state
                    last_transition_idx = i

        return transitions

    def _smooth_regimes(self, states, min_duration=10):
        """
        Smooth regime predictions by requiring minimum duration in each state.

        If a regime lasts less than min_duration days, it gets merged with
        the previous regime.
        """
        smoothed = states.copy()
        i = 0

        while i < len(smoothed):
            current_state = smoothed[i]

            # Find how long we stay in this state
            j = i
            while j < len(smoothed) and smoothed[j] == current_state:
                j += 1

            duration = j - i

            # If too short, merge with previous state
            if duration < min_duration and i > 0:
                prev_state = smoothed[i - 1]
                smoothed[i:j] = prev_state

            i = j

        return smoothed

    def _characterize_base_states(self, features_df, hidden_states):
        """Characterize the 2 base HMM states."""
        df = features_df.copy()
        df['state'] = hidden_states

        print(f"\n{'=' * 80}")
        print("BASE STATE CHARACTERISTICS (2-State HMM)")
        print(f"{'=' * 80}")
        print(f"{'State':<10} {'Mean Return':<12} {'Volatility':<12} {'Days':<8} {'Freq %':<8}")
        print("-" * 80)

        for state in range(2):
            mask = df['state'] == state
            mean_return = df.loc[mask, 'SPY_log_returns'].mean()
            volatility = df.loc[mask, 'SPY_log_returns'].std()
            count = mask.sum()
            freq_pct = (count / len(df)) * 100

            print(f"State {state:<4} {mean_return * 100:>10.3f}% {volatility * 100:>10.3f}% "
                  f"{count:>8} {freq_pct:>7.1f}%")

    def _calculate_regime_statistics(self, features_df, regime_array):
        """Calculate statistics for the 5 probability-based regimes."""
        df = features_df.copy()
        df['regime'] = regime_array

        print(f"\n{'=' * 80}")
        print("PROBABILITY-BASED REGIME CHARACTERISTICS (with Recovery sub-classification)")
        print(f"{'=' * 80}")
        print(f"{'Regime':<15} {'Mean Return':<12} {'Volatility':<12} {'Days':<8} {'Freq %':<8}")
        print("-" * 80)

        regime_stats = {}
        for regime in ['Risk-On', 'Recovery', 'Pivot+', 'Pivot-', 'Risk-Off']:
            mask = df['regime'] == regime
            if mask.sum() > 0:
                stats = {
                    'mean_return': df.loc[mask, 'SPY_log_returns'].mean(),
                    'volatility': df.loc[mask, 'SPY_log_returns'].std(),
                    'count': mask.sum()
                }
                regime_stats[regime] = stats

                freq_pct = (stats['count'] / len(df)) * 100
                print(f"{regime:<15} {stats['mean_return'] * 100:>10.3f}% "
                      f"{stats['volatility'] * 100:>10.3f}% "
                      f"{stats['count']:>8} {freq_pct:>7.1f}%")

        self.regime_stats = regime_stats

    def analyze_probability_transitions(self, regimes, features_df, target_date=None, window_days=30):
        """
        Analyze probability transitions around a specific date or major regime changes.

        Args:
            regimes: Series with regime classifications
            features_df: DataFrame with features
            target_date: Specific date to analyze (default: None = analyze all major transitions)
            window_days: Days before/after to show (default: 30)
        """
        if not hasattr(self, 'state_probabilities'):
            print("No probability data available")
            return

        # Find major transitions (where regime changes)
        regime_changes = []
        for i in range(1, len(regimes)):
            if regimes.iloc[i] != regimes.iloc[i - 1]:
                regime_changes.append(i)

        print(f"\n{'=' * 80}")
        print("PROBABILITY TRANSITION ANALYSIS")
        print(f"{'=' * 80}")
        print(f"Found {len(regime_changes)} regime changes")

        # If target_date specified, find closest transition
        if target_date is not None:
            target_dt = pd.to_datetime(target_date)
            closest_idx = None
            min_diff = float('inf')

            for idx in regime_changes:
                diff = abs((regimes.index[idx] - target_dt).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    closest_idx = idx

            if closest_idx is not None:
                print(f"\nAnalyzing transition closest to {target_date}:")
                self._print_transition_window(regimes, features_df, closest_idx, window_days)
        else:
            # Show first few major transitions
            print(f"\nShowing first 3 major transitions:")
            for i, idx in enumerate(regime_changes[:3]):
                print(f"\n{'-' * 80}")
                print(f"Transition #{i + 1}:")
                self._print_transition_window(regimes, features_df, idx, window_days=15)

        # Also check for any days in the 40-60% probability range
        bull_probs = self.state_probabilities[:, 0]  # Assume state 0 is one of them
        max_probs = np.maximum(bull_probs, 1 - bull_probs)  # Get max probability

        uncertain_days = np.where((max_probs >= 0.4) & (max_probs <= 0.6))[0]

        print(f"\n{'-' * 80}")
        print(f"DAYS WITH UNCERTAIN PROBABILITIES (40-60% range):")
        print(f"Total uncertain days: {len(uncertain_days)}")

        if len(uncertain_days) > 0:
            print(f"\nFirst 10 uncertain days:")
            print(f"{'Date':<12} {'Regime':<15} {'Bull Prob':<12} {'Bear Prob':<12}")
            print("-" * 60)
            for idx in uncertain_days[:10]:
                date = regimes.index[idx]
                regime = regimes.iloc[idx]
                bull_prob = bull_probs[idx]
                bear_prob = 1 - bull_prob
                print(f"{date.strftime('%Y-%m-%d'):<12} {regime:<15} {bull_prob:>10.1%} {bear_prob:>10.1%}")
        else:
            print("  No days found with probabilities in the 40-60% range")
            print("  The HMM model is making very confident predictions (>60% or <40%)")
            print("  This suggests clear regime separation in the features")

        print(f"{'=' * 80}\n")

    def _print_transition_window(self, regimes, features_df, center_idx, window_days=15):
        """Print detailed probability info around a transition."""
        start_idx = max(0, center_idx - window_days)
        end_idx = min(len(regimes), center_idx + window_days + 1)

        transition_date = regimes.index[center_idx]
        from_regime = regimes.iloc[center_idx - 1]
        to_regime = regimes.iloc[center_idx]

        print(f"  Date: {transition_date.strftime('%Y-%m-%d')}")
        print(f"  Transition: {from_regime} → {to_regime}")
        print(f"\n  Probability progression (±{window_days} days):")
        print(f"  {'Date':<12} {'Regime':<15} {'Bull Prob':<12} {'SPY Change':<12}")
        print(f"  {'-' * 60}")

        for i in range(start_idx, end_idx):
            date = regimes.index[i]
            regime = regimes.iloc[i]
            bull_prob = self.state_probabilities[i, 0]  # First state probability

            spy_return = features_df.iloc[i]['SPY_log_returns'] * 100 if i < len(features_df) else 0

            # Highlight the transition day
            marker = " ← TRANSITION" if i == center_idx else ""

            print(f"  {date.strftime('%Y-%m-%d'):<12} {regime:<15} {bull_prob:>10.1%} "
                  f"{spy_return:>+10.2f}%{marker}")

    def print_current_state(self, regimes, features_df, lookback_days=20):

        """
        Print a comprehensive summary of the current market state.

        Args:
            regimes: Series with regime classifications
            features_df: DataFrame with features
            lookback_days: Number of days to analyze for recent trends
        """
        if len(regimes) == 0:
            print("No regime data available")
            return

        current_regime = regimes.iloc[-1]
        current_date = regimes.index[-1]

        # Get the last state probability
        if hasattr(self, 'state_probabilities') and len(self.state_probabilities) > 0:
            last_probs = self.state_probabilities[-1]
            bull_prob = max(last_probs)  # Highest probability
            bear_prob = min(last_probs)  # Lowest probability
        else:
            bull_prob = None
            bear_prob = None

        # Calculate recent statistics
        recent_data = features_df.iloc[-lookback_days:]
        recent_return = (recent_data['SPY_Close'].iloc[-1] / recent_data['SPY_Close'].iloc[0] - 1) * 100
        recent_vol = recent_data['SPY_log_returns'].std() * np.sqrt(252) * 100
        recent_drawdown = recent_data['drawdown'].iloc[-1] * 100 if 'drawdown' in recent_data.columns else None

        # Find regime changes in recent period
        recent_regimes = regimes.iloc[-lookback_days:]
        regime_changes = (recent_regimes != recent_regimes.shift()).sum() - 1

        # Count days in current regime
        days_in_regime = 1
        for i in range(len(regimes) - 2, -1, -1):
            if regimes.iloc[i] == current_regime:
                days_in_regime += 1
            else:
                break

        print(f"\n{'=' * 80}")
        print("CURRENT MARKET STATE SUMMARY")
        print(f"{'=' * 80}")
        print(f"Date: {current_date.strftime('%Y-%m-%d')}")
        print(f"Current Regime: {current_regime}")
        print(f"Days in Current Regime: {days_in_regime}")

        if bull_prob is not None:
            print(f"\nState Probabilities:")
            print(f"  Risk-On Probability: {bull_prob:.1%}")
            print(f"  Risk-Off Probability: {bear_prob:.1%}")

        print(f"\nRecent Performance ({lookback_days} days):")
        print(f"  SPY Return: {recent_return:+.2f}%")
        print(f"  Annualized Volatility: {recent_vol:.2f}%")
        if recent_drawdown is not None:
            print(f"  Current Drawdown: {recent_drawdown:.2f}%")
        print(f"  Regime Changes: {regime_changes}")

        # Show regime interpretation
        print(f"\nRegime Interpretation:")
        if current_regime == 'Risk-On':
            print("  Market is in a confirmed bullish state with strong upward momentum.")
            print("  Strategies: Favor long positions, growth stocks, and risk assets.")
        elif current_regime == 'Recovery':
            print("  Market is in recovery mode: High volatility but positive returns.")
            print("  Strategies: Cautious risk-taking, favor quality/resilient names over aggressive growth.")
            print("  Note: This is a Risk-Off classification with improving fundamentals.")
        elif current_regime == 'Risk-Off':
            print("  Market is in a confirmed bearish state with defensive positioning.")
            print("  Strategies: Reduce exposure, favor defensive sectors, consider hedges.")
        elif current_regime == 'Pivot+':
            print("  Market is transitioning from Risk-Off toward Risk-On.")
            print("  Strategies: Begin adding risk exposure as confidence builds.")
        elif current_regime == 'Pivot-':
            print("  Market is transitioning from Risk-On toward Risk-Off.")
            print("  Strategies: Consider reducing risk exposure and taking profits.")

        print(f"{'=' * 80}\n")

    def detect_regime_transitions(self, regimes, min_duration=10):
        """Detect regime transitions with persistence requirement for cleaner signals."""
        if len(regimes) < min_duration:
            return []

        transitions = []
        confirmed_regime = regimes.iloc[0]

        for i in range(min_duration, len(regimes)):
            recent_regimes = regimes.iloc[i - min_duration + 1:i + 1]

            if (recent_regimes == regimes.iloc[i]).all():
                current_regime = regimes.iloc[i]

                if current_regime != confirmed_regime:
                    transition_start_idx = i - min_duration + 1

                    if transitions:
                        duration_in_old = transition_start_idx - transitions[-1]['transition_start_idx']
                    else:
                        duration_in_old = transition_start_idx

                    transitions.append({
                        'date': regimes.index[i],
                        'transition_start_date': regimes.index[transition_start_idx],
                        'from_regime': confirmed_regime,
                        'to_regime': current_regime,
                        'duration_in_old': duration_in_old,
                        'transition_start_idx': transition_start_idx,
                        'confirmation_idx': i
                    })

                    confirmed_regime = current_regime

        return transitions

    def plot_results(self, spy_data, features_df, regimes, transitions=None):
        """Create comprehensive visualization."""
        if transitions is None:
            transitions = self.detect_regime_transitions(regimes, min_duration=10)

        print(f"\nDetected {len(transitions)} regime transitions (10+ day persistence)")

        fig, axes = plt.subplots(3, 1, figsize=(18, 10), sharex=True)

        spy_close = spy_data['Close'] if isinstance(spy_data['Close'], pd.Series) else spy_data['Close'].squeeze()
        spy_aligned = spy_close.loc[features_df.index]

        # Get colors
        unique_regimes = regimes.unique()
        color_map = {regime: self.regime_colors.get(regime, '#888888') for regime in unique_regimes}

        # 1. SPY Price with regimes
        ax = axes[0]

        # Plot each regime with appropriate marker size and style
        for regime in unique_regimes:
            mask = regimes == regime

            if regime in ['Pivot+', 'Pivot-']:
                # Use larger, more visible dots for pivot states
                ax.scatter(features_df.index[mask], spy_aligned[mask],
                           c=color_map[regime], s=20, alpha=0.9, label=regime,
                           marker='o', edgecolors='black', linewidths=0.5, zorder=5)
            else:
                # Use smaller dots for Risk-On/Risk-Off states
                ax.scatter(features_df.index[mask], spy_aligned[mask],
                           c=color_map[regime], s=3, alpha=0.7, label=regime, zorder=3)

        for trans in transitions:
            ax.axvline(x=trans['date'], color='red', linestyle=':', alpha=0.5, linewidth=1.5, zorder=2)

        ax.set_ylabel('SPY Price ($)', fontsize=11, fontweight='bold')
        ax.set_title(f'HMM Market Regime Classification (Probability-Based: Risk-On/Risk-Off/Pivot)\n' +
                     'Larger dots indicate Pivot states (transition zones)',
                     fontsize=13, fontweight='bold')
        ax.legend(loc='upper left', fontsize=9, ncol=2)
        ax.grid(True, alpha=0.3, zorder=1)

        # 2. Regime timeline
        ax = axes[1]
        current_regime = regimes.iloc[0]
        start_idx = 0

        for i in range(1, len(regimes)):
            if regimes.iloc[i] != current_regime or i == len(regimes) - 1:
                end_idx = min(i, len(regimes) - 1)
                ax.axvspan(regimes.index[start_idx], regimes.index[end_idx],
                           facecolor=color_map[current_regime], alpha=0.7)
                current_regime = regimes.iloc[i]
                start_idx = i

        for trans in transitions:
            ax.axvline(x=trans['date'], color='red', linestyle='-', linewidth=2, alpha=0.8)

        ax.set_ylabel('Regime', fontsize=10, fontweight='bold')
        ax.set_yticks([])
        ax.grid(True, alpha=0.3, axis='x')

        # 3. SPY Log Returns
        ax = axes[2]
        ax.plot(features_df.index, features_df['SPY_log_returns'] * 100,
                color='blue', linewidth=0.6, alpha=0.7)
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax.fill_between(features_df.index, 0, features_df['SPY_log_returns'] * 100,
                        where=(features_df['SPY_log_returns'] >= 0), color='green', alpha=0.2)
        ax.fill_between(features_df.index, 0, features_df['SPY_log_returns'] * 100,
                        where=(features_df['SPY_log_returns'] < 0), color='red', alpha=0.2)
        ax.set_ylabel('SPY Log Returns (%)', fontsize=10, fontweight='bold')
        ax.set_xlabel('Date', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)

        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

        start_date = features_df.index[0].strftime('%Y-%m-%d')
        end_date = features_df.index[-1].strftime('%Y-%m-%d')
        fig.suptitle(f'HMM Regime Analysis with Multivariate Features: {start_date} to {end_date}\n'
                     f'Transitions: {len(transitions)} | Probability-based classification (>60% Risk-On, <40% Risk-Off)',
                     fontsize=14, fontweight='bold')

        plt.tight_layout(rect=[0, 0.02, 1, 0.97])
        plt.savefig('hmm_regime_classification.png', dpi=300, bbox_inches='tight')
        print("Saved: hmm_regime_classification.png")

        return fig


def main():
    """Main demonstration."""
    # Download data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=20 * 365)  # 20 years

    spy_data = download_data(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )

    print(f"\n{'=' * 80}")
    print("HMM REGIME CLASSIFICATION - PROBABILITY-BASED (RISK-ON/RISK-OFF)")
    print(f"{'=' * 80}")

    # Initialize classifier
    classifier = HMMRegimeClassifier(n_regimes=2)

    # Prepare features
    features_df = classifier.prepare_features(spy_data, use_multivariate=True)

    # Fit and classify - 2-state HMM with probability-based regime classification
    regimes = classifier.fit_and_classify(
        features_df,
        use_multivariate=True,
        min_regime_duration=10,  # Default 10 days minimum in each regime to confirm transition
        use_recovery=True #include a recovery state classification: high vol/increasing returns
    )

    # Detect transitions
    transitions = classifier.detect_regime_transitions(regimes, min_duration=10)

    # Print transition summary
    print(f"\n{'=' * 80}")
    print(f"REGIME TRANSITIONS (14-day persistence)")
    print(f"{'=' * 80}")
    if transitions:
        print(f"{'Date':<12} {'From':<15} {'To':<15} {'Days in Old':<12}")
        print("-" * 80)
        for trans in transitions:
            print(f"{trans['date'].strftime('%Y-%m-%d'):<12} {trans['from_regime']:<15} "
                  f"{trans['to_regime']:<15} {trans['duration_in_old']:<12}")
    else:
        print("No transitions detected")

    # Print current market state
    classifier.print_current_state(regimes, features_df, lookback_days=20)

    # Analyze probability transitions (especially around major events like COVID crash)
    print("\n" + "=" * 80)
    print("ANALYZING MAJOR TRANSITIONS")
    print("=" * 80)
    classifier.analyze_probability_transitions(regimes, features_df, target_date='2020-03-15', window_days=30)

    # Also show general transition analysis
    classifier.analyze_probability_transitions(regimes, features_df, target_date=None, window_days=10)

    # Plot
    print("\nCreating visualization...")
    fig = classifier.plot_results(spy_data, features_df, regimes, transitions)

    print(f"\n{'=' * 80}")
    print("Analysis complete!")
    print(f"{'=' * 80}")

    return classifier, features_df, regimes, transitions


if __name__ == "__main__":
    classifier, features_df, regimes, transitions = main()
