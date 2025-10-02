#!/usr/bin/env python3
"""Business Unit: utilities | Status: current.

Stress Test Script for The Alchemiser Trading System.

This script runs comprehensive stress testing by:
1. Running the trading system with real Alpaca Paper API
2. Liquidating all positions
3. Mocking different market conditions (RSI values, prices)
4. Iterating through all possible market scenarios
5. Logging outcomes and detecting edge cases

The script uses real Alpaca Paper trading endpoints and is expected
to have a runtime of 1+ hours as it iterates through all market conditions.

Market conditions are simulated by mocking the IndicatorService to return
controlled RSI values and prices for all symbols used in strategy CLJ files.

Usage:
    python scripts/stress_test.py [--quick] [--dry-run]

Options:
    --quick     Run a subset of scenarios for faster testing (10 scenarios)
    --dry-run   Skip actual trading system execution, just show plan
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, ClassVar
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from the_alchemiser.main import main
from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from the_alchemiser.shared.schemas.technical_indicator import TechnicalIndicator
from the_alchemiser.shared.services.alpaca_trading_service import AlpacaTradingService

# Configure logging
configure_application_logging()
logger = get_logger(__name__)


@dataclass
class MarketCondition:
    """Represents a specific market condition scenario.

    Each scenario has a unique identifier and specific RSI/price ranges
    for all symbols used in the strategies.
    """

    scenario_id: str
    description: str
    rsi_range: tuple[float, float]  # (min, max) for RSI values
    price_multiplier: float  # Multiplier for base prices (e.g., 0.8 = -20%, 1.2 = +20%)
    volatility_regime: str  # "low", "medium", "high"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StressTestResult:
    """Result from a single stress test scenario."""

    scenario_id: str
    timestamp: datetime
    success: bool
    trades_executed: int
    error_message: str | None = None
    error_type: str | None = None
    portfolio_value: float | None = None
    execution_time_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class MockIndicatorService:
    """Mock IndicatorService that returns controlled values for stress testing.

    This service returns indicator values based on the current market condition
    scenario, allowing us to test all possible market states.
    """

    def __init__(self, market_condition: MarketCondition) -> None:
        """Initialize mock indicator service with a market condition.

        Args:
            market_condition: The market condition to simulate

        """
        self.market_condition = market_condition
        self.call_count = 0

    def get_indicator(self, request: IndicatorRequest) -> TechnicalIndicator:
        """Return controlled indicator values based on market condition.

        Args:
            request: Indicator request

        Returns:
            TechnicalIndicator with controlled values

        """
        self.call_count += 1

        symbol = request.symbol
        indicator_type = request.indicator_type
        parameters = request.parameters

        # Generate deterministic but varied values based on scenario
        rsi_min, rsi_max = self.market_condition.rsi_range
        # Use symbol hash for deterministic variation within range
        symbol_hash = sum(ord(c) for c in symbol)
        rsi_offset = (symbol_hash % 20) - 10  # +/- 10 from midpoint
        rsi_midpoint = (rsi_min + rsi_max) / 2
        rsi_value = max(rsi_min, min(rsi_max, rsi_midpoint + rsi_offset))

        # Base price with multiplier and symbol variation
        base_price = 100.0 + (symbol_hash % 50)
        current_price = base_price * self.market_condition.price_multiplier

        # Create indicator based on type
        if indicator_type == "rsi":
            window = int(parameters.get("window", 14))
            return TechnicalIndicator(
                symbol=symbol,
                timestamp=datetime.now(UTC),
                rsi_14=rsi_value if window == 14 else None,
                rsi_10=rsi_value if window == 10 else None,
                rsi_20=rsi_value if window == 20 else None,
                rsi_21=rsi_value if window == 21 else None,
                current_price=Decimal(str(current_price)),
                data_source="stress_test_mock",
                metadata={
                    "value": rsi_value,
                    "window": window,
                    "scenario": self.market_condition.scenario_id,
                },
            )

        if indicator_type == "current_price":
            return TechnicalIndicator(
                symbol=symbol,
                timestamp=datetime.now(UTC),
                current_price=Decimal(str(current_price)),
                data_source="stress_test_mock",
                metadata={
                    "value": current_price,
                    "scenario": self.market_condition.scenario_id,
                },
            )

        # For other indicators, return reasonable defaults
        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(UTC),
            current_price=Decimal(str(current_price)),
            data_source="stress_test_mock",
            metadata={"scenario": self.market_condition.scenario_id},
        )


class StressTestRunner:
    """Orchestrates stress testing across multiple market conditions."""

    # All symbols extracted from CLJ strategy files
    ALL_SYMBOLS: ClassVar[list[str]] = [
        "ABSI",
        "ACHR",
        "AEHR",
        "AMZN",
        "APLD",
        "APP",
        "ARM",
        "ARQQ",
        "AVGO",
        "BBAI",
        "BE",
        "BIL",
        "BITF",
        "BITX",
        "BULZ",
        "BWXT",
        "CCJ",
        "CEG",
        "COIN",
        "CONL",
        "COP",
        "CORZ",
        "COST",
        "CRM",
        "CRNC",
        "DBC",
        "DBO",
        "EEM",
        "EVLV",
        "EXC",
        "FAS",
        "FCG",
        "FFAI",
        "FTNT",
        "GE",
        "GLD",
        "HOOD",
        "IEF",
        "IEI",
        "IONQ",
        "IOO",
        "IREN",
        "IWM",
        "JOBY",
        "KMLM",
        "LAES",
        "LEU",
        "LLY",
        "MARA",
        "MRVL",
        "MSFT",
        "MSTR",
        "NFLX",
        "NLR",
        "NLSP",
        "NNE",
        "NVDA",
        "NVDL",
        "NVO",
        "OKLO",
        "ORCL",
        "PGR",
        "PLTR",
        "PLUG",
        "PSQ",
        "QBTS",
        "QMCO",
        "QQQ",
        "QQQE",
        "QS",
        "QSI",
        "QUBT",
        "RGTI",
        "RIOT",
        "RKLB",
        "RZLV",
        "SERV",
        "SES",
        "SHV",
        "SHY",
        "SIDU",
        "SMR",
        "SNOW",
        "SOUN",
        "SOXL",
        "SPY",
        "SPXL",
        "SQQQ",
        "TAN",
        "TECL",
        "TEM",
        "TLT",
        "TMF",
        "TMV",
        "TQQQ",
        "UCO",
        "UEC",
        "UNG",
        "UPRO",
        "URTY",
        "UVXY",
        "VIXM",
        "VIXY",
        "VNOM",
        "VOOG",
        "VOOV",
        "VOX",
        "VRSN",
        "WKEY",
        "WULF",
        "XME",
        "ZS",
    ]

    def __init__(self, *, quick_mode: bool = False, dry_run: bool = False) -> None:
        """Initialize stress test runner.

        Args:
            quick_mode: If True, run only a subset of scenarios
            dry_run: If True, don't execute actual trades

        """
        self.quick_mode = quick_mode
        self.dry_run = dry_run
        self.results: list[StressTestResult] = []
        self.logger = logger

    def generate_market_conditions(self) -> list[MarketCondition]:
        """Generate all market condition scenarios to test.

        Returns:
            List of market conditions covering the full range of possibilities

        """
        conditions = []

        # Define RSI regimes
        rsi_regimes = [
            ("oversold", (0, 30)),
            ("neutral_low", (30, 50)),
            ("neutral_mid", (45, 55)),
            ("neutral_high", (50, 70)),
            ("overbought", (70, 100)),
            ("extreme_overbought", (79, 100)),  # Critical threshold in strategies
        ]

        # Define price movement scenarios
        price_scenarios = [
            ("crash", 0.5, "high"),  # -50% crash with high volatility
            ("bear", 0.8, "medium"),  # -20% bear market
            ("flat", 1.0, "low"),  # Flat market
            ("bull", 1.2, "medium"),  # +20% bull market
            ("boom", 1.5, "high"),  # +50% boom
        ]

        # Generate combinations
        for scenario_num, ((rsi_name, rsi_range), (price_name, multiplier, volatility)) in enumerate(
            itertools.product(rsi_regimes, price_scenarios), start=1
        ):
            conditions.append(
                MarketCondition(
                    scenario_id=f"scenario_{scenario_num:03d}",
                    description=f"RSI {rsi_name} ({rsi_range[0]:.0f}-{rsi_range[1]:.0f}) + Price {price_name} ({multiplier:.1%}) + {volatility} volatility",
                    rsi_range=rsi_range,
                    price_multiplier=multiplier,
                    volatility_regime=volatility,
                    metadata={
                        "rsi_regime": rsi_name,
                        "price_regime": price_name,
                    },
                )
            )

        # Add edge case scenarios
        conditions.extend([
            MarketCondition(
                scenario_id="edge_all_oversold_crash",
                description="All symbols oversold + market crash (extreme bearish)",
                rsi_range=(0, 20),
                price_multiplier=0.3,
                volatility_regime="extreme",
                metadata={"edge_case": True, "type": "extreme_bearish"},
            ),
            MarketCondition(
                scenario_id="edge_all_overbought_boom",
                description="All symbols overbought + market boom (extreme bullish)",
                rsi_range=(85, 100),
                price_multiplier=2.0,
                volatility_regime="extreme",
                metadata={"edge_case": True, "type": "extreme_bullish"},
            ),
            MarketCondition(
                scenario_id="edge_threshold_79",
                description="All symbols at RSI 79 threshold (decision boundary)",
                rsi_range=(78, 80),
                price_multiplier=1.0,
                volatility_regime="medium",
                metadata={"edge_case": True, "type": "threshold_79"},
            ),
            MarketCondition(
                scenario_id="edge_threshold_75",
                description="All symbols at RSI 75 threshold (decision boundary)",
                rsi_range=(74, 76),
                price_multiplier=1.0,
                volatility_regime="medium",
                metadata={"edge_case": True, "type": "threshold_75"},
            ),
        ])

        if self.quick_mode:
            # In quick mode, sample every 3rd scenario plus all edge cases
            regular_scenarios = [c for c in conditions if not c.metadata.get("edge_case")]
            edge_scenarios = [c for c in conditions if c.metadata.get("edge_case")]
            conditions = regular_scenarios[::3] + edge_scenarios

        return conditions

    def liquidate_all_positions(self) -> bool:
        """Liquidate all positions using AlpacaTradingService.

        Returns:
            True if liquidation successful or no positions, False on error

        """
        if self.dry_run:
            self.logger.info("DRY RUN: Would liquidate all positions")
            return True

        try:
            self.logger.info("Liquidating all positions before scenario run")
            settings = load_settings()

            # Create trading service directly
            from alpaca.trading.client import TradingClient

            trading_client = TradingClient(
                api_key=settings.alpaca.key or "",
                secret_key=settings.alpaca.secret or "",
                paper=settings.alpaca.paper_trading,
            )

            # For stress test, we don't need real websocket manager
            from unittest.mock import Mock

            mock_websocket_manager = Mock()

            trading_service = AlpacaTradingService(
                trading_client=trading_client,
                websocket_manager=mock_websocket_manager,
                paper_trading=settings.alpaca.paper_trading,
            )
            result = trading_service.close_all_positions(cancel_orders=True)

            if result:
                self.logger.info(
                    f"Successfully liquidated {len(result)} positions",
                    positions_closed=len(result),
                )
            else:
                self.logger.info("No positions to liquidate (account already empty)")

            # Wait a bit for positions to settle
            time.sleep(2)
            return True

        except Exception as e:
            self.logger.error(f"Failed to liquidate positions: {e}", error=str(e))
            return False

    def run_scenario(self, condition: MarketCondition) -> StressTestResult:
        """Run a single stress test scenario.

        Args:
            condition: Market condition to test

        Returns:
            Result of the stress test scenario

        """
        start_time = time.time()
        self.logger.info(
            f"Running scenario {condition.scenario_id}: {condition.description}",
            scenario_id=condition.scenario_id,
            description=condition.description,
        )

        if self.dry_run:
            self.logger.info(f"DRY RUN: Would execute scenario {condition.scenario_id}")
            return StressTestResult(
                scenario_id=condition.scenario_id,
                timestamp=datetime.now(UTC),
                success=True,
                trades_executed=0,
                execution_time_seconds=time.time() - start_time,
                metadata={"dry_run": True},
            )

        try:
            # Mock the IndicatorService to return controlled values
            mock_indicator_service = MockIndicatorService(condition)

            # Patch IndicatorService at the point of instantiation
            with patch(
                "the_alchemiser.strategy_v2.engines.dsl.engine.IndicatorService"
            ) as mock_indicator_class:
                # Make the mock class return our mock instance
                mock_indicator_class.return_value = mock_indicator_service

                # Run the trading system
                result = main(["trade"])

                # Extract result data
                success = getattr(result, "success", False)
                trades_executed = getattr(result, "trades_executed", 0)
                portfolio_value = getattr(result, "total_portfolio_value", None)

                execution_time = time.time() - start_time

                test_result = StressTestResult(
                    scenario_id=condition.scenario_id,
                    timestamp=datetime.now(UTC),
                    success=success,
                    trades_executed=trades_executed,
                    portfolio_value=portfolio_value,
                    execution_time_seconds=execution_time,
                    metadata={
                        "rsi_range": condition.rsi_range,
                        "price_multiplier": condition.price_multiplier,
                        "volatility_regime": condition.volatility_regime,
                        "indicator_calls": mock_indicator_service.call_count,
                    },
                )

                self.logger.info(
                    f"Scenario {condition.scenario_id} completed",
                    success=success,
                    trades_executed=trades_executed,
                    execution_time=f"{execution_time:.2f}s",
                )

                return test_result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(
                f"Scenario {condition.scenario_id} failed with error",
                error=str(e),
                error_type=type(e).__name__,
            )

            return StressTestResult(
                scenario_id=condition.scenario_id,
                timestamp=datetime.now(UTC),
                success=False,
                trades_executed=0,
                error_message=str(e),
                error_type=type(e).__name__,
                execution_time_seconds=execution_time,
                metadata={"exception": str(e)},
            )

    def run_all_scenarios(self) -> list[StressTestResult]:
        """Run all stress test scenarios.

        Returns:
            List of results from all scenarios

        """
        conditions = self.generate_market_conditions()
        total_scenarios = len(conditions)

        self.logger.info(
            f"Starting stress test with {total_scenarios} scenarios",
            total_scenarios=total_scenarios,
            quick_mode=self.quick_mode,
            dry_run=self.dry_run,
        )

        results = []
        for i, condition in enumerate(conditions, 1):
            self.logger.info(
                f"Progress: {i}/{total_scenarios} scenarios",
                progress=f"{i}/{total_scenarios}",
                percentage=f"{100*i/total_scenarios:.1f}%",
            )

            # Liquidate positions before each scenario
            if not self.liquidate_all_positions():
                self.logger.warning(
                    f"Failed to liquidate positions before scenario {condition.scenario_id}"
                )

            # Run the scenario
            result = self.run_scenario(condition)
            results.append(result)

            # Small delay between scenarios to avoid rate limits
            if not self.dry_run and i < total_scenarios:
                time.sleep(5)

        self.results = results
        return results

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive stress test report.

        Returns:
            Dictionary with test results and statistics

        """
        if not self.results:
            return {"error": "No results available"}

        total_scenarios = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = total_scenarios - successful
        total_trades = sum(r.trades_executed for r in self.results)
        total_time = sum(r.execution_time_seconds for r in self.results)

        # Group failures by error type
        failures_by_type: dict[str, int] = {}
        for result in self.results:
            if not result.success and result.error_type:
                failures_by_type[result.error_type] = (
                    failures_by_type.get(result.error_type, 0) + 1
                )

        # Find edge cases
        edge_case_results = [
            {
                "scenario_id": r.scenario_id,
                "success": r.success,
                "trades": r.trades_executed,
                "error": r.error_message,
            }
            for r in self.results
            if r.metadata and "edge_case" in str(r.metadata)
        ]

        return {
            "summary": {
                "total_scenarios": total_scenarios,
                "successful": successful,
                "failed": failed,
                "success_rate": f"{100 * successful / total_scenarios:.2f}%",
                "total_trades_executed": total_trades,
                "total_execution_time_seconds": round(total_time, 2),
                "average_time_per_scenario": round(total_time / total_scenarios, 2),
            },
            "failures_by_type": failures_by_type,
            "edge_case_results": edge_case_results,
            "failed_scenarios": [
                {
                    "scenario_id": r.scenario_id,
                    "error_type": r.error_type,
                    "error_message": r.error_message,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.results
                if not r.success
            ],
            "timestamp": datetime.now(UTC).isoformat(),
            "quick_mode": self.quick_mode,
            "dry_run": self.dry_run,
        }

    def save_results(self, output_file: str = "stress_test_results.json") -> None:
        """Save stress test results to JSON file.

        Args:
            output_file: Path to output file

        """
        report = self.generate_report()

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Stress test results saved to {output_path}")

    def print_summary(self) -> None:
        """Print human-readable summary of stress test results."""
        report = self.generate_report()

        print("\n" + "=" * 80)
        print("STRESS TEST SUMMARY")
        print("=" * 80)

        summary = report["summary"]
        print(f"\nTotal Scenarios:    {summary['total_scenarios']}")
        print(f"Successful:         {summary['successful']}")
        print(f"Failed:             {summary['failed']}")
        print(f"Success Rate:       {summary['success_rate']}")
        print(f"Total Trades:       {summary['total_trades_executed']}")
        print(f"Total Time:         {summary['total_execution_time_seconds']:.2f}s")
        print(f"Avg Time/Scenario:  {summary['average_time_per_scenario']:.2f}s")

        if report["failures_by_type"]:
            print("\nFailures by Type:")
            for error_type, count in report["failures_by_type"].items():
                print(f"  {error_type}: {count}")

        if report["edge_case_results"]:
            print("\nEdge Case Results:")
            for edge in report["edge_case_results"]:
                status = "✓" if edge["success"] else "✗"
                print(
                    f"  {status} {edge['scenario_id']}: "
                    f"{edge['trades']} trades"
                    + (f" - ERROR: {edge['error']}" if edge.get("error") else "")
                )

        print("\n" + "=" * 80)


def main_cli() -> int:
    """Run stress test CLI entry point.

    Returns:
        Exit code (0 for success, 1 for failure)

    """
    parser = argparse.ArgumentParser(
        description="Stress test The Alchemiser trading system across all market conditions"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick test with subset of scenarios (10 scenarios)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - show plan without executing trades",
    )
    parser.add_argument(
        "--output",
        default="stress_test_results.json",
        help="Output file for results (default: stress_test_results.json)",
    )

    args = parser.parse_args()

    # Verify environment
    if not args.dry_run and not os.getenv("ALPACA_KEY") and not os.getenv("ALPACA_API_KEY"):
        print("ERROR: ALPACA_KEY or ALPACA_API_KEY environment variable not set")
        print("Please set your Alpaca Paper API credentials")
        return 1

    # Run stress test
    runner = StressTestRunner(quick_mode=args.quick, dry_run=args.dry_run)

    print("\n" + "=" * 80)
    print("THE ALCHEMISER - STRESS TEST")
    print("=" * 80)
    print(f"\nMode: {'DRY RUN' if args.dry_run else 'LIVE PAPER TRADING'}")
    print(f"Scenarios: {'Quick (~10)' if args.quick else 'Full (~34)'}")
    print(f"Output: {args.output}")
    print("\n" + "=" * 80 + "\n")

    if args.dry_run:
        # In dry run, just show the plan
        conditions = runner.generate_market_conditions()
        print(f"\nWould execute {len(conditions)} scenarios:\n")
        for i, condition in enumerate(conditions, 1):
            print(f"{i:3d}. {condition.scenario_id}: {condition.description}")
        print("\nUse without --dry-run to execute actual stress test")
        return 0

    # Execute full stress test
    start_time = time.time()
    results = runner.run_all_scenarios()
    total_time = time.time() - start_time

    # Save and print results
    runner.save_results(args.output)
    runner.print_summary()

    print(f"\nTotal execution time: {total_time / 60:.1f} minutes")
    print(f"Results saved to: {args.output}\n")

    # Return success if all scenarios passed
    return 0 if all(r.success for r in results) else 1


if __name__ == "__main__":
    sys.exit(main_cli())
