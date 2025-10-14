"""Business Unit: utilities | Status: current.

Stress test runner orchestration.

Main orchestrator for stress testing across multiple market conditions,
supporting both liquidation and stateful modes.
"""

from __future__ import annotations

import itertools
import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from the_alchemiser.main import main
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.logging import get_logger

from .analysis import StressTestReporter
from .mocking import MockIndicatorService
from .models import (
    MarketCondition,
    PortfolioState,
    PortfolioTransition,
    StressTestResult,
)

logger = get_logger(__name__)


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

    def __init__(
        self,
        *,
        quick_mode: bool = False,
        dry_run: bool = False,
        stateful_mode: bool = False,
    ) -> None:
        """Initialize stress test runner.

        Args:
            quick_mode: If True, run only a subset of scenarios
            dry_run: If True, don't execute actual trades
            stateful_mode: If True, maintain portfolio state across scenarios

        """
        self.quick_mode = quick_mode
        self.dry_run = dry_run
        self.stateful_mode = stateful_mode
        self.results: list[StressTestResult] = []
        self.portfolio_states: list[PortfolioState] = []
        self.transitions: list[PortfolioTransition] = []
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
        for scenario_num, (
            (rsi_name, rsi_range),
            (price_name, multiplier, volatility),
        ) in enumerate(itertools.product(rsi_regimes, price_scenarios), start=1):
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
        conditions.extend(
            [
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
            ]
        )

        if self.quick_mode:
            # In quick mode, sample every 3rd scenario plus all edge cases
            regular_scenarios = [c for c in conditions if not c.metadata.get("edge_case")]
            edge_scenarios = [c for c in conditions if c.metadata.get("edge_case")]
            conditions = regular_scenarios[::3] + edge_scenarios

        return conditions

    def liquidate_all_positions(self) -> bool:
        """Liquidate all positions using AlpacaManager.

        Returns:
            True if liquidation successful or no positions, False on error

        """
        if self.dry_run:
            self.logger.info("DRY RUN: Would liquidate all positions")
            return True

        try:
            self.logger.info("Liquidating all positions before scenario run")

            # Use proper credential loading
            api_key, secret_key, _ = get_alpaca_keys()
            if not api_key or not secret_key:
                self.logger.error("Alpaca credentials not found in environment")
                return False

            # Stress test always uses paper trading to avoid live execution
            paper_trading = True

            # Create AlpacaManager which handles proper service initialization
            alpaca_manager = AlpacaManager(
                api_key=api_key,
                secret_key=secret_key,
                paper=paper_trading,
            )

            # Use the trading service from AlpacaManager
            result = alpaca_manager.close_all_positions(cancel_orders=True)

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

    def capture_portfolio_state(
        self, scenario_id: str, alpaca_manager: AlpacaManager | None = None
    ) -> PortfolioState:
        """Capture current portfolio state.

        Args:
            scenario_id: ID of the scenario
            alpaca_manager: Optional AlpacaManager instance to use

        Returns:
            PortfolioState snapshot

        """
        if self.dry_run:
            # Return mock portfolio state for dry run
            return PortfolioState(
                scenario_id=scenario_id,
                timestamp=datetime.now(UTC),
                positions={},
                market_values={},
                cash_balance=Decimal("100000"),
                total_value=Decimal("100000"),
                allocation_percentages={},
            )

        try:
            # Get current account and positions
            if not alpaca_manager:
                api_key, secret_key, _ = get_alpaca_keys()
                if not api_key or not secret_key:
                    raise ValueError("Alpaca credentials not available")
                # Stress test always uses paper trading to avoid live execution
                paper_trading = True
                alpaca_manager = AlpacaManager(
                    api_key=api_key,
                    secret_key=secret_key,
                    paper=paper_trading,
                )

            account = alpaca_manager.get_account_object()
            if not account:
                raise ValueError("Failed to get account")

            positions_list = alpaca_manager.get_positions()

            # Build positions dict
            positions: dict[str, Decimal] = {}
            market_values: dict[str, Decimal] = {}
            allocation_percentages: dict[str, float] = {}

            total_equity = Decimal(str(account.equity))

            for pos in positions_list:
                symbol = pos.symbol
                qty = Decimal(str(pos.qty))
                market_value = Decimal(str(pos.market_value))

                positions[symbol] = qty
                market_values[symbol] = market_value

                if total_equity > 0:
                    allocation_percentages[symbol] = float((market_value / total_equity) * 100)

            cash_balance = Decimal(str(account.cash))
            total_value = Decimal(str(account.equity))

            return PortfolioState(
                scenario_id=scenario_id,
                timestamp=datetime.now(UTC),
                positions=positions,
                market_values=market_values,
                cash_balance=cash_balance,
                total_value=total_value,
                allocation_percentages=allocation_percentages,
            )

        except Exception as e:
            self.logger.error(f"Failed to capture portfolio state: {e}", error=str(e))
            # Return empty state on error
            return PortfolioState(
                scenario_id=scenario_id,
                timestamp=datetime.now(UTC),
                positions={},
                market_values={},
                cash_balance=Decimal("0"),
                total_value=Decimal("0"),
                allocation_percentages={},
            )

    def calculate_transition(
        self,
        from_state: PortfolioState,
        to_state: PortfolioState,
        trades_executed: int,
        execution_time: float,
    ) -> PortfolioTransition:
        """Calculate portfolio transition between two states.

        Args:
            from_state: Starting portfolio state
            to_state: Ending portfolio state
            trades_executed: Number of trades executed
            execution_time: Execution time in seconds

        Returns:
            PortfolioTransition object

        """
        # Determine symbol changes
        from_symbols = set(from_state.positions.keys())
        to_symbols = set(to_state.positions.keys())

        symbols_added = list(to_symbols - from_symbols)
        symbols_removed = list(from_symbols - to_symbols)
        symbols_adjusted = [
            s
            for s in (from_symbols & to_symbols)
            if from_state.positions[s] != to_state.positions[s]
        ]

        # Calculate rebalance percentage (portfolio turnover)
        total_changed_value = Decimal("0")
        for symbol in symbols_removed:
            total_changed_value += abs(from_state.market_values.get(symbol, Decimal("0")))
        for symbol in symbols_added:
            total_changed_value += abs(to_state.market_values.get(symbol, Decimal("0")))
        for symbol in symbols_adjusted:
            from_value = from_state.market_values.get(symbol, Decimal("0"))
            to_value = to_state.market_values.get(symbol, Decimal("0"))
            total_changed_value += abs(to_value - from_value)

        rebalance_percentage = 0.0
        if from_state.total_value > 0:
            rebalance_percentage = float((total_changed_value / from_state.total_value) * 100)

        # Estimate turnover cost (simplified: 0.1% of changed value)
        turnover_cost = total_changed_value * Decimal("0.001")

        return PortfolioTransition(
            from_scenario=from_state.scenario_id,
            to_scenario=to_state.scenario_id,
            trades_executed=trades_executed,
            symbols_added=symbols_added,
            symbols_removed=symbols_removed,
            symbols_adjusted=symbols_adjusted,
            rebalance_percentage=rebalance_percentage,
            turnover_cost=turnover_cost,
            execution_time=execution_time,
        )

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
            stateful_mode=self.stateful_mode,
        )

        results = []
        previous_state: PortfolioState | None = None

        for i, condition in enumerate(conditions, 1):
            self.logger.info(
                f"Progress: {i}/{total_scenarios} scenarios",
                progress=f"{i}/{total_scenarios}",
                percentage=f"{100 * i / total_scenarios:.1f}%",
            )

            # In liquidation mode, liquidate positions before each scenario
            # In stateful mode, skip liquidation to maintain portfolio state
            if not self.stateful_mode and not self.liquidate_all_positions():
                self.logger.warning(
                    f"Failed to liquidate positions before scenario {condition.scenario_id}"
                )

            # Capture portfolio state before scenario (for stateful mode)
            if self.stateful_mode:
                before_state = self.capture_portfolio_state(f"{condition.scenario_id}_before")
                if previous_state is None:
                    # First scenario - store as initial state
                    previous_state = before_state

            # Run the scenario
            result = self.run_scenario(condition)
            results.append(result)

            # Capture portfolio state after scenario (for stateful mode)
            if self.stateful_mode and not self.dry_run:
                after_state = self.capture_portfolio_state(condition.scenario_id)
                self.portfolio_states.append(after_state)

                # Calculate transition
                if previous_state:
                    transition = self.calculate_transition(
                        previous_state,
                        after_state,
                        result.trades_executed,
                        result.execution_time_seconds,
                    )
                    self.transitions.append(transition)

                # Update previous state for next iteration
                previous_state = after_state

            # Small delay between scenarios to avoid rate limits
            if not self.dry_run and i < total_scenarios:
                time.sleep(5)

        self.results = results
        return results

    def get_reporter(self) -> StressTestReporter:
        """Get reporter instance with current results.

        Returns:
            StressTestReporter instance

        """
        return StressTestReporter(
            results=self.results,
            quick_mode=self.quick_mode,
            dry_run=self.dry_run,
            stateful_mode=self.stateful_mode,
            portfolio_states=self.portfolio_states,
            transitions=self.transitions,
        )
