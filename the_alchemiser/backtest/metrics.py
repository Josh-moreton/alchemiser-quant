#!/usr/bin/env python3
"""
Performance Metrics Calculator for Backtest Engine

This module handles all performance metric calculations including:
- Total return, CAGR, volatility
- Sharpe ratio, Calmar ratio
- Maximum drawdown calculations
- Risk-adjusted performance metrics
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class PerformanceMetrics:
    """Container for all performance metrics"""

    total_return: float
    cagr: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    trading_days: int
    final_equity: float

    def __str__(self) -> str:
        return (
            f"Return: {self.total_return:.2f}%, CAGR: {self.cagr:.2f}%, "
            f"Volatility: {self.volatility:.2f}%, Sharpe: {self.sharpe_ratio:.2f}, "
            f"Max DD: {self.max_drawdown:.2f}%, Calmar: {self.calmar_ratio:.2f}"
        )


class MetricsCalculator:
    """Calculator for backtest performance metrics"""

    @staticmethod
    def calculate_performance_metrics(
        equity_curve: list[float],
        initial_equity: float,
        trading_days: int,
        risk_free_rate: float = 0.02,
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics from equity curve

        Args:
            equity_curve: List of daily equity values
            initial_equity: Starting equity amount
            trading_days: Number of trading days
            risk_free_rate: Risk-free rate for Sharpe ratio calculation

        Returns:
            PerformanceMetrics object with all calculated metrics
        """
        if len(equity_curve) < 2:
            return PerformanceMetrics(
                total_return=0.0,
                cagr=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                calmar_ratio=0.0,
                trading_days=0,
                final_equity=initial_equity,
            )

        final_equity = equity_curve[-1]

        # Basic return metrics
        total_return = (final_equity / initial_equity - 1) * 100

        # Time-based metrics
        n_years = trading_days / 252.0 if trading_days > 0 else 1
        cagr = ((final_equity / initial_equity) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0

        # Risk metrics
        daily_returns = [
            equity_curve[i] / equity_curve[i - 1] - 1 for i in range(1, len(equity_curve))
        ]

        if len(daily_returns) > 1:
            volatility = np.std(daily_returns) * np.sqrt(252) * 100  # Annualized volatility %
            mean_daily_return = np.mean(daily_returns)
            excess_return = mean_daily_return - (risk_free_rate / 252)  # Daily risk-free rate
            sharpe_ratio = (
                (excess_return / np.std(daily_returns)) * np.sqrt(252)
                if np.std(daily_returns) > 0
                else 0
            )
        else:
            volatility = 0.0
            sharpe_ratio = 0.0

        # Maximum drawdown calculation
        max_drawdown = MetricsCalculator.calculate_max_drawdown(equity_curve)

        # Calmar ratio (CAGR / Max Drawdown)
        calmar_ratio = cagr / abs(max_drawdown) if abs(max_drawdown) > 0.01 else float("inf")

        return PerformanceMetrics(
            total_return=total_return,
            cagr=cagr,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            trading_days=trading_days,
            final_equity=final_equity,
        )

    @staticmethod
    def calculate_max_drawdown(equity_curve: list[float]) -> float:
        """
        Calculate maximum drawdown from equity curve

        Args:
            equity_curve: List of daily equity values

        Returns:
            Maximum drawdown as percentage (negative value)
        """
        if len(equity_curve) < 2:
            return 0.0

        peak = equity_curve[0]
        max_drawdown = 0.0

        for equity in equity_curve[1:]:
            if equity > peak:
                peak = equity

            drawdown = (equity - peak) / peak * 100
            if drawdown < max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    @staticmethod
    def calculate_rolling_sharpe(
        equity_curve: list[float], window: int = 252, risk_free_rate: float = 0.02
    ) -> list[float]:
        """
        Calculate rolling Sharpe ratio

        Args:
            equity_curve: List of daily equity values
            window: Rolling window size in days
            risk_free_rate: Annual risk-free rate

        Returns:
            List of rolling Sharpe ratios
        """
        if len(equity_curve) < window + 1:
            return []

        # Calculate daily returns
        daily_returns = [
            equity_curve[i] / equity_curve[i - 1] - 1 for i in range(1, len(equity_curve))
        ]

        rolling_sharpe = []
        daily_rf_rate = risk_free_rate / 252

        for i in range(window - 1, len(daily_returns)):
            window_returns = daily_returns[i - window + 1 : i + 1]

            if len(window_returns) == window:
                mean_return = np.mean(window_returns)
                std_return = np.std(window_returns)

                if std_return > 0:
                    excess_return = mean_return - daily_rf_rate
                    sharpe = (excess_return / std_return) * np.sqrt(252)
                    rolling_sharpe.append(sharpe)
                else:
                    rolling_sharpe.append(0.0)
            else:
                rolling_sharpe.append(0.0)

        return rolling_sharpe

    @staticmethod
    def calculate_monthly_returns(
        equity_curve: list[float], dates: list[pd.Timestamp]
    ) -> pd.DataFrame:
        """
        Calculate monthly return breakdown

        Args:
            equity_curve: List of daily equity values
            dates: List of corresponding dates

        Returns:
            DataFrame with monthly returns
        """
        if len(equity_curve) != len(dates):
            raise ValueError("Equity curve and dates must have same length")

        df = pd.DataFrame({"equity": equity_curve, "date": dates})
        df.set_index("date", inplace=True)

        # Resample to monthly and calculate returns
        monthly_equity = df.resample("M")["equity"].last()
        monthly_returns = monthly_equity.pct_change().dropna()

        return pd.DataFrame(
            {
                "month": [date.strftime("%Y-%m") for date in monthly_returns.index],
                "return_pct": [ret * 100 for ret in monthly_returns.values],
            }
        )

    @staticmethod
    def compare_strategies(results: list[tuple[str, PerformanceMetrics]]) -> pd.DataFrame:
        """
        Create comparison table of multiple strategies

        Args:
            results: List of (strategy_name, metrics) tuples

        Returns:
            DataFrame comparing all strategies
        """
        comparison_data = []

        for strategy_name, metrics in results:
            comparison_data.append(
                {
                    "Strategy": strategy_name,
                    "Total Return %": metrics.total_return,
                    "CAGR %": metrics.cagr,
                    "Volatility %": metrics.volatility,
                    "Sharpe Ratio": metrics.sharpe_ratio,
                    "Max Drawdown %": metrics.max_drawdown,
                    "Calmar Ratio": metrics.calmar_ratio,
                    "Final Equity": metrics.final_equity,
                    "Trading Days": metrics.trading_days,
                }
            )

        df = pd.DataFrame(comparison_data)

        # Sort by Calmar ratio (handle infinity values)
        df["_calmar_sort"] = df["Calmar Ratio"].replace([np.inf, -np.inf], 9999)
        df = df.sort_values("_calmar_sort", ascending=False)
        df = df.drop("_calmar_sort", axis=1)

        return df
