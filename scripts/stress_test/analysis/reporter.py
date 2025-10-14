"""Business Unit: utilities | Status: current.

Report generation for stress testing.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..models.portfolio_state import PortfolioState, PortfolioTransition
from ..models.results import StressTestResult


class StressTestReporter:
    """Generates comprehensive stress test reports."""

    def __init__(
        self,
        results: list[StressTestResult],
        quick_mode: bool = False,  # noqa: FBT001, FBT002
        dry_run: bool = False,  # noqa: FBT001, FBT002
        stateful_mode: bool = False,  # noqa: FBT001, FBT002
        portfolio_states: list[PortfolioState] | None = None,
        transitions: list[PortfolioTransition] | None = None,
    ) -> None:
        """Initialize reporter with test results.

        Args:
            results: List of test results
            quick_mode: Whether quick mode was used
            dry_run: Whether dry run mode was used
            stateful_mode: Whether stateful mode was used
            portfolio_states: List of portfolio states (for stateful mode)
            transitions: List of portfolio transitions (for stateful mode)

        """
        self.results = results
        self.quick_mode = quick_mode
        self.dry_run = dry_run
        self.stateful_mode = stateful_mode
        self.portfolio_states = portfolio_states or []
        self.transitions = transitions or []

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
                failures_by_type[result.error_type] = failures_by_type.get(result.error_type, 0) + 1

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

        report: dict[str, Any] = {
            "summary": {
                "total_scenarios": total_scenarios,
                "successful": successful,
                "failed": failed,
                "success_rate": f"{100 * successful / total_scenarios:.2f}%",
                "total_trades_executed": total_trades,
                "total_execution_time_seconds": round(total_time, 2),
                "average_time_per_scenario": round(total_time / total_scenarios, 2),
                "mode": "stateful" if self.stateful_mode else "liquidation",
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

        # Add stateful mode specific data
        if self.stateful_mode:
            report["stateful_analysis"] = self._generate_stateful_analysis()

        return report

    def _generate_stateful_analysis(self) -> dict[str, Any]:
        """Generate analysis specific to stateful mode.

        Returns:
            Dictionary with stateful mode analysis

        """
        if not self.portfolio_states or not self.transitions:
            return {"error": "No portfolio state data available"}

        total_transitions = len(self.transitions)
        total_rebalance_percentage = sum(t.rebalance_percentage for t in self.transitions)
        avg_rebalance_percentage = (
            total_rebalance_percentage / total_transitions if total_transitions > 0 else 0.0
        )

        total_turnover_cost = sum(t.turnover_cost for t in self.transitions)

        # Analyze symbol changes
        symbols_added_total = sum(len(t.symbols_added) for t in self.transitions)
        symbols_removed_total = sum(len(t.symbols_removed) for t in self.transitions)
        symbols_adjusted_total = sum(len(t.symbols_adjusted) for t in self.transitions)

        return {
            "total_transitions": total_transitions,
            "average_rebalance_percentage": round(avg_rebalance_percentage, 2),
            "total_turnover_cost": str(total_turnover_cost),
            "symbols_added_total": symbols_added_total,
            "symbols_removed_total": symbols_removed_total,
            "symbols_adjusted_total": symbols_adjusted_total,
            "portfolio_states_count": len(self.portfolio_states),
            "transitions": [t.to_dict() for t in self.transitions],
        }

    def print_summary(self) -> None:
        """Print human-readable summary of stress test results."""
        report = self.generate_report()

        print("\n" + "=" * 80)
        print("STRESS TEST SUMMARY")
        print("=" * 80)

        summary = report["summary"]
        print(f"\nMode:               {summary['mode']}")
        print(f"Total Scenarios:    {summary['total_scenarios']}")
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

        # Print stateful mode analysis
        if self.stateful_mode and "stateful_analysis" in report:
            analysis = report["stateful_analysis"]
            if "error" not in analysis:
                print("\nStateful Mode Analysis:")
                print(f"  Total Transitions:        {analysis['total_transitions']}")
                print(
                    f"  Avg Rebalance %:          {analysis['average_rebalance_percentage']:.2f}%"
                )
                print(f"  Total Turnover Cost:      {analysis['total_turnover_cost']}")
                print(f"  Symbols Added (Total):    {analysis['symbols_added_total']}")
                print(f"  Symbols Removed (Total):  {analysis['symbols_removed_total']}")
                print(f"  Symbols Adjusted (Total): {analysis['symbols_adjusted_total']}")

        print("\n" + "=" * 80)
