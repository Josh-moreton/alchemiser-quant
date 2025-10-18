"""Business Unit: notifications | Status: current.

Tests for normalization in the notifications adapter.

Covers:
- Mapping StrategySignal.reasoning -> reason for templates
- Flattening ConsolidatedPortfolio DTO dumps to flat symbol->weight dict
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.notifications_v2.service import _ExecutionResultAdapter
from the_alchemiser.shared.events.schemas import TradingNotificationRequested


def _base_event(execution_data: dict[str, object]) -> TradingNotificationRequested:
    return TradingNotificationRequested(
        correlation_id="cid-1",
        causation_id="cause-1",
        event_id="evt-1",
        timestamp=datetime.now(UTC),
        source_module="tests",
        source_component="tests",
        trading_success=True,
        trading_mode="PAPER",
        orders_placed=0,
        orders_succeeded=0,
        total_trade_value=Decimal("0.00"),
        execution_data=execution_data,
    )


class TestNormalization:
    def test_reasoning_is_mapped_to_reason(self) -> None:
        event = _base_event(
            {
                "strategy_signals": {
                    "Nuclear": {
                        "signal": "bullish",
                        "confidence": 0.9,
                        "reasoning": "RuleA AND RuleB -> pick SPY",
                    },
                    "Phoenix": {"signal": "neutral", "confidence": 0.5},
                }
            }
        )

        adapter = _ExecutionResultAdapter(event)

        assert "Nuclear" in adapter.strategy_signals
        # reasoning should be copied to reason, preserving value
        assert adapter.strategy_signals["Nuclear"]["reason"] == "RuleA AND RuleB -> pick SPY"
        # existing reason is left unchanged if present; Phoenix has none, remains without
        assert "reason" not in adapter.strategy_signals["Phoenix"]

    def test_flatten_consolidated_portfolio_from_dto_dump(self) -> None:
        event = _base_event(
            {
                "consolidated_portfolio": {
                    "schema_version": "1.0",
                    "target_allocations": {"SPY": 0.6, "BND": 0.4},
                    "metadata": {"source": "dsl"},
                }
            }
        )

        adapter = _ExecutionResultAdapter(event)

        # Adapter should expose flat mapping expected by templates
        assert adapter.consolidated_portfolio == {"SPY": 0.6, "BND": 0.4}

    def test_flatten_consolidated_portfolio_fallback_from_execution_summary(self) -> None:
        event = _base_event(
            {
                # Missing top-level consolidated_portfolio; present inside execution_summary
                "execution_summary": {
                    "orders_placed": 1,
                    "consolidated_portfolio": {"target_allocations": {"GLD": 0.1, "QQQ": 0.9}},
                }
            }
        )

        adapter = _ExecutionResultAdapter(event)

        assert adapter.consolidated_portfolio == {"GLD": 0.1, "QQQ": 0.9}
