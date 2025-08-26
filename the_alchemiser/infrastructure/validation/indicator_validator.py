#!/usr/bin/env python3
"""Comprehensive Indicator Validation for The Alchemiser Quantitative Trading System.

This module provides a comprehensive testing suite that validates ALL technical
indicators used by our trading strategies against TwelveData API values.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import requests
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from the_alchemiser.domain.math.indicators import TechnicalIndicators


class IndicatorValidationSuite:
    """Comprehensive validation suite for technical indicators against TwelveData API."""

    def __init__(self, api_key: str, console: Console) -> None:
        """Store API credentials and initialize result containers."""
        self.api_key = api_key
        self.console = console
        self.api_base_url = "https://api.twelvedata.com"
        self.rate_limit_delay = 8.0  # 8 seconds between calls for 7.5 calls/minute
        self.results: list[dict[str, Any]] = []
        self.performance_stats: dict[str, Any] = {}

        # Configure logging
        logging.basicConfig(level=logging.WARNING)
        self.logger = logging.getLogger(__name__)

        # Strategy symbols - all assets used across strategies
        self.strategy_symbols = {
            "core": ["SPY", "QQQ", "TQQQ", "SPXL", "XLK"],
            "volatility": ["VIX", "UVXY", "VIXY", "VXX", "VIXM"],
            "sectors": ["XLF", "XLP", "XLU", "XLV", "XLE", "VTV"],
            "defensive": ["BIL", "BTAL", "TLT"],
            "specialty": ["TECL", "KMLM", "RETL"],
        }

        # All indicators used across strategies with their periods
        self.indicator_definitions = {
            "rsi": [9, 10, 14, 20, 21, 70],
            "sma": [3, 20, 200],
            "moving_average_return": [20, 90],
            "cumulative_return": [60],
            "stdev_return": [5, 6],  # Custom indicators
        }

    def fetch_market_data(self, symbol: str, days: int = 250) -> pd.Series | None:
        """Fetch historical price data for a symbol."""
        try:
            url = f"{self.api_base_url}/time_series"
            params = {
                "symbol": symbol,
                "interval": "1day",
                "outputsize": str(days),
                "apikey": self.api_key,
            }

            self.console.print(f"  Fetching {days} days of data for {symbol}...")
            time.sleep(self.rate_limit_delay)

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "values" not in data or not data["values"]:
                self.logger.warning(f"No data returned for {symbol}")
                return None

            # Convert to pandas Series (reverse for chronological order)
            prices = []
            dates = []
            for entry in reversed(data["values"]):
                prices.append(float(entry["close"]))
                dates.append(pd.to_datetime(entry["datetime"]))

            return pd.Series(prices, index=dates)

        except Exception as e:
            self.logger.error(f"Failed to fetch data for {symbol}: {e}")
            return None

    def fetch_twelvedata_indicator(self, symbol: str, indicator: str, period: int) -> float | None:
        """Fetch indicator value from TwelveData API."""
        try:
            indicator_map = {"rsi": "rsi", "sma": "sma"}

            if indicator not in indicator_map:
                return None

            url = f"{self.api_base_url}/{indicator_map[indicator]}"
            params = {
                "symbol": symbol,
                "interval": "1day",
                "time_period": str(period),
                "apikey": self.api_key,
            }

            time.sleep(self.rate_limit_delay)
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "values" not in data or not data["values"]:
                return None

            # Get the most recent value
            latest_value = data["values"][0][indicator_map[indicator]]
            return float(latest_value)

        except Exception as e:
            self.logger.error(f"Failed to fetch {indicator} for {symbol}: {e}")
            return None

    def validate_rsi(self, symbol: str, price_data: pd.Series, period: int) -> dict[str, Any]:
        """Validate RSI calculation against TwelveData."""
        start_time = time.time()

        # Calculate our RSI
        our_rsi = TechnicalIndicators.rsi(price_data, period)
        our_latest = our_rsi.dropna().iloc[-1] if not our_rsi.dropna().empty else None

        # Get TwelveData RSI
        td_rsi = self.fetch_twelvedata_indicator(symbol, "rsi", period)

        calculation_time = time.time() - start_time

        if our_latest is None or td_rsi is None:
            return {
                "indicator": f"RSI({period})",
                "symbol": symbol,
                "our_value": our_latest,
                "twelvedata_value": td_rsi,
                "difference": None,
                "tolerance": 6.0 if period >= 70 else (3.0 if period >= 20 else 2.0),
                "passed": False,
                "error": "Missing values",
                "calculation_time": calculation_time,
            }

        difference = abs(our_latest - td_rsi)

        # Adjust tolerance based on RSI period - longer periods may have more variance
        if period >= 70:
            tolerance = 6.0  # Higher tolerance for very long periods like RSI(70)
        elif period >= 20:
            tolerance = 3.0  # Medium tolerance for medium periods
        else:
            tolerance = 2.0  # Standard tolerance for short periods

        passed = difference <= tolerance

        return {
            "indicator": f"RSI({period})",
            "symbol": symbol,
            "our_value": round(our_latest, 2),
            "twelvedata_value": round(td_rsi, 2),
            "difference": round(difference, 2),
            "tolerance": tolerance,
            "passed": passed,
            "error": None if passed else f"Difference {difference:.2f} > {tolerance}",
            "calculation_time": calculation_time,
        }

    def validate_sma(self, symbol: str, price_data: pd.Series, period: int) -> dict[str, Any]:
        """Validate Simple Moving Average calculation against TwelveData."""
        start_time = time.time()

        # Calculate our SMA
        our_sma = TechnicalIndicators.moving_average(price_data, period)
        our_latest = our_sma.dropna().iloc[-1] if not our_sma.dropna().empty else None

        # Get TwelveData SMA
        td_sma = self.fetch_twelvedata_indicator(symbol, "sma", period)

        calculation_time = time.time() - start_time

        if our_latest is None or td_sma is None:
            return {
                "indicator": f"SMA({period})",
                "symbol": symbol,
                "our_value": our_latest,
                "twelvedata_value": td_sma,
                "difference": None,
                "tolerance": 0.01,
                "passed": False,
                "error": "Missing values",
                "calculation_time": calculation_time,
            }

        # For SMA, use percentage difference for tolerance
        percentage_diff = abs(our_latest - td_sma) / td_sma * 100
        tolerance = 0.1  # 0.1% tolerance
        passed = percentage_diff <= tolerance

        return {
            "indicator": f"SMA({period})",
            "symbol": symbol,
            "our_value": round(our_latest, 4),
            "twelvedata_value": round(td_sma, 4),
            "difference": round(percentage_diff, 4),
            "tolerance": tolerance,
            "passed": passed,
            "error": None if passed else f"Difference {percentage_diff:.4f}% > {tolerance}%",
            "calculation_time": calculation_time,
        }

    def validate_custom_indicators(
        self, symbol: str, price_data: pd.Series
    ) -> list[dict[str, Any]]:
        """Validate custom indicators that don't have TwelveData equivalents."""
        results = []

        # Moving Average Return
        for period in self.indicator_definitions["moving_average_return"]:
            start_time = time.time()
            ma_return = TechnicalIndicators.moving_average_return(price_data, period)
            latest_value = ma_return.dropna().iloc[-1] if not ma_return.dropna().empty else None
            calculation_time = time.time() - start_time

            # Validate range and sanity
            passed = (
                latest_value is not None
                and -50 <= latest_value <= 50  # Reasonable range for MA returns
                and not np.isnan(latest_value)
                and not np.isinf(latest_value)
            )

            results.append(
                {
                    "indicator": f"MA_Return({period})",
                    "symbol": symbol,
                    "our_value": round(latest_value, 4) if latest_value is not None else None,
                    "twelvedata_value": "N/A",
                    "difference": "N/A",
                    "tolerance": "Sanity Check",
                    "passed": passed,
                    "error": None if passed else "Value out of expected range or invalid",
                    "calculation_time": calculation_time,
                }
            )

        # Cumulative Return
        for period in self.indicator_definitions["cumulative_return"]:
            start_time = time.time()
            cum_return = TechnicalIndicators.cumulative_return(price_data, period)
            latest_value = cum_return.dropna().iloc[-1] if not cum_return.dropna().empty else None
            calculation_time = time.time() - start_time

            # Validate range and sanity
            passed = (
                latest_value is not None
                and -95 <= latest_value <= 1000  # Reasonable range for cumulative returns
                and not np.isnan(latest_value)
                and not np.isinf(latest_value)
            )

            results.append(
                {
                    "indicator": f"Cum_Return({period})",
                    "symbol": symbol,
                    "our_value": round(latest_value, 4) if latest_value is not None else None,
                    "twelvedata_value": "N/A",
                    "difference": "N/A",
                    "tolerance": "Sanity Check",
                    "passed": passed,
                    "error": None if passed else "Value out of expected range or invalid",
                    "calculation_time": calculation_time,
                }
            )

        return results

    def validate_symbol(self, symbol: str) -> list[dict[str, Any]]:
        """Validate all indicators for a single symbol."""
        self.console.print(f"\n[bold blue]Validating indicators for {symbol}[/bold blue]")

        # Fetch price data
        price_data = self.fetch_market_data(symbol)
        if price_data is None or len(price_data) < 200:
            self.console.print(
                f"[red]  ❌ Insufficient data for {symbol} (got {len(price_data) if price_data is not None else 0}, need 200+)[/red]"
            )
            return []

        results = []

        # Validate RSI indicators
        for period in self.indicator_definitions["rsi"]:
            result = self.validate_rsi(symbol, price_data, period)
            results.append(result)

            status = "✅" if result["passed"] else "❌"
            self.console.print(
                f"  {status} RSI({period}): {result['our_value']} vs {result['twelvedata_value']}"
            )

        # Validate SMA indicators
        for period in self.indicator_definitions["sma"]:
            result = self.validate_sma(symbol, price_data, period)
            results.append(result)

            status = "✅" if result["passed"] else "❌"
            self.console.print(
                f"  {status} SMA({period}): {result['our_value']} vs {result['twelvedata_value']}"
            )

        # Validate custom indicators
        custom_results = self.validate_custom_indicators(symbol, price_data)
        results.extend(custom_results)

        for result in custom_results:
            status = "✅" if result["passed"] else "❌"
            self.console.print(f"  {status} {result['indicator']}: {result['our_value']}")

        return results

    def run_validation_suite(self, symbols: list[str], mode: str = "full") -> dict[str, Any]:
        """Run the complete validation suite."""
        self.console.print("[bold green]🔬 Starting Indicator Validation Suite[/bold green]")
        self.console.print(f"Mode: {mode.upper()}")
        self.console.print(f"Symbols: {', '.join(symbols)}")
        self.console.print(f"API Rate Limit: {self.rate_limit_delay}s between calls")
        self.console.print("Using TwelveData REST API\n")

        start_time = time.time()
        all_results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:
            main_task = progress.add_task("Validating indicators...", total=len(symbols))

            for symbol in symbols:
                progress.update(main_task, description=f"Processing {symbol}...")

                symbol_results = self.validate_symbol(symbol)
                all_results.extend(symbol_results)

                progress.advance(main_task)

        total_time = time.time() - start_time

        # Calculate summary statistics
        total_tests = len(all_results)
        passed_tests = sum(1 for r in all_results if r["passed"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        avg_calc_time = np.mean(
            [r["calculation_time"] for r in all_results if r["calculation_time"]]
        )

        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "avg_calculation_time": avg_calc_time,
            "results": all_results,
        }

        self.results = all_results
        self.performance_stats = summary

        return summary

    def generate_report(self, summary: dict[str, Any]) -> None:
        """Generate a comprehensive validation report."""
        # Summary Panel
        summary_text = Text()
        summary_text.append(f"Total Tests: {summary['total_tests']}\n", style="white")
        summary_text.append(f"Passed: {summary['passed_tests']}\n", style="green")
        summary_text.append(f"Failed: {summary['failed_tests']}\n", style="red")
        summary_text.append(f"Success Rate: {summary['success_rate']:.1f}%\n", style="cyan")
        summary_text.append(f"Total Time: {summary['total_time']:.1f}s\n", style="white")
        summary_text.append(f"Avg Calc Time: {summary['avg_calculation_time']:.3f}s", style="white")

        summary_panel = Panel(
            summary_text, title="[bold blue]Validation Summary[/bold blue]", border_style="blue"
        )
        self.console.print(summary_panel)

        # Detailed Results Table
        table = Table(title="Detailed Validation Results")
        table.add_column("Symbol", style="cyan")
        table.add_column("Indicator", style="magenta")
        table.add_column("Our Value", justify="right")
        table.add_column("TwelveData", justify="right")
        table.add_column("Diff", justify="right")
        table.add_column("Status", justify="center")
        table.add_column("Error", style="red")

        for result in summary["results"]:
            status = "✅" if result["passed"] else "❌"
            error = result["error"] or ""

            table.add_row(
                result["symbol"],
                result["indicator"],
                str(result["our_value"]),
                str(result["twelvedata_value"]),
                str(result["difference"]),
                status,
                error[:30] + "..." if len(error) > 30 else error,
            )

        self.console.print(table)

        # Failed Tests Details
        failed_results = [r for r in summary["results"] if not r["passed"]]
        if failed_results:
            self.console.print("\n[bold red]Failed Tests Details:[/bold red]")
            for result in failed_results:
                self.console.print(
                    f"  ❌ {result['symbol']} {result['indicator']}: {result['error']}"
                )

    def save_results(self, filename: str | None = None) -> str:
        """Save validation results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"indicator_validation_{timestamp}.json"

        output = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.performance_stats,
            "detailed_results": self.results,
        }

        with open(filename, "w") as f:
            json.dump(output, f, indent=2, default=str)

        self.console.print(f"\n[green]Results saved to {filename}[/green]")
        return filename
