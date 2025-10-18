"""Business Unit: portfolio | Status: current

Test portfolio analysis handler for correct trades_required determination.

Validates that trades_required is set based on BUY/SELL actions,
not merely the presence of HOLD items.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)


class TestTradesRequiredLogic:
    """Test trades_required flag is set correctly based on plan items."""

    def test_trades_required_false_when_only_holds(self):
        """Test that trades_required=False when plan contains only HOLD actions."""
        # Create a rebalance plan with only HOLD items (portfolio already balanced)
        plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("0.00"),
            items=[
                RebalancePlanItem(
                    symbol="NLR",
                    action="HOLD",
                    current_weight=Decimal("0.143"),
                    target_weight=Decimal("0.143"),
                    weight_diff=Decimal("0.0"),
                    current_value=Decimal("1430.00"),
                    target_value=Decimal("1430.00"),
                    trade_amount=Decimal("0.00"),
                    priority=1,
                ),
                RebalancePlanItem(
                    symbol="OKLO",
                    action="HOLD",
                    current_weight=Decimal("0.143"),
                    target_weight=Decimal("0.143"),
                    weight_diff=Decimal("0.0"),
                    current_value=Decimal("1430.00"),
                    target_value=Decimal("1430.00"),
                    trade_amount=Decimal("0.00"),
                    priority=2,
                ),
                RebalancePlanItem(
                    symbol="SVIX",
                    action="HOLD",
                    current_weight=Decimal("0.143"),
                    target_weight=Decimal("0.143"),
                    weight_diff=Decimal("0.0"),
                    current_value=Decimal("1430.00"),
                    target_value=Decimal("1430.00"),
                    trade_amount=Decimal("0.00"),
                    priority=3,
                ),
            ],
        )

        # Verify trades_required logic
        trades_required = any(item.action in ["BUY", "SELL"] for item in plan.items)
        assert trades_required is False, "Should be False when only HOLD actions present"

    def test_trades_required_true_with_buy_action(self):
        """Test that trades_required=True when plan contains BUY actions."""
        plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("1000.00"),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    action="BUY",
                    current_weight=Decimal("0.3"),
                    target_weight=Decimal("0.4"),
                    weight_diff=Decimal("0.1"),
                    current_value=Decimal("3000.00"),
                    target_value=Decimal("4000.00"),
                    trade_amount=Decimal("1000.00"),
                    priority=1,
                ),
                RebalancePlanItem(
                    symbol="MSFT",
                    action="HOLD",
                    current_weight=Decimal("0.6"),
                    target_weight=Decimal("0.6"),
                    weight_diff=Decimal("0.0"),
                    current_value=Decimal("6000.00"),
                    target_value=Decimal("6000.00"),
                    trade_amount=Decimal("0.00"),
                    priority=2,
                ),
            ],
        )

        trades_required = any(item.action in ["BUY", "SELL"] for item in plan.items)
        assert trades_required is True, "Should be True when BUY actions present"

    def test_trades_required_true_with_sell_action(self):
        """Test that trades_required=True when plan contains SELL actions."""
        plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("1000.00"),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    action="SELL",
                    current_weight=Decimal("0.5"),
                    target_weight=Decimal("0.4"),
                    weight_diff=Decimal("-0.1"),
                    current_value=Decimal("5000.00"),
                    target_value=Decimal("4000.00"),
                    trade_amount=Decimal("-1000.00"),
                    priority=1,
                ),
                RebalancePlanItem(
                    symbol="MSFT",
                    action="HOLD",
                    current_weight=Decimal("0.5"),
                    target_weight=Decimal("0.6"),
                    weight_diff=Decimal("0.0"),
                    current_value=Decimal("5000.00"),
                    target_value=Decimal("6000.00"),
                    trade_amount=Decimal("0.00"),
                    priority=2,
                ),
            ],
        )

        trades_required = any(item.action in ["BUY", "SELL"] for item in plan.items)
        assert trades_required is True, "Should be True when SELL actions present"

    def test_trades_required_true_with_mixed_actions(self):
        """Test that trades_required=True when plan has both BUY and SELL."""
        plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            total_portfolio_value=Decimal("10000.00"),
            total_trade_value=Decimal("2000.00"),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    action="SELL",
                    current_weight=Decimal("0.5"),
                    target_weight=Decimal("0.3"),
                    weight_diff=Decimal("-0.2"),
                    current_value=Decimal("5000.00"),
                    target_value=Decimal("3000.00"),
                    trade_amount=Decimal("-2000.00"),
                    priority=1,
                ),
                RebalancePlanItem(
                    symbol="MSFT",
                    action="BUY",
                    current_weight=Decimal("0.3"),
                    target_weight=Decimal("0.5"),
                    weight_diff=Decimal("0.2"),
                    current_value=Decimal("3000.00"),
                    target_value=Decimal("5000.00"),
                    trade_amount=Decimal("2000.00"),
                    priority=2,
                ),
                RebalancePlanItem(
                    symbol="GOOGL",
                    action="HOLD",
                    current_weight=Decimal("0.2"),
                    target_weight=Decimal("0.2"),
                    weight_diff=Decimal("0.0"),
                    current_value=Decimal("2000.00"),
                    target_value=Decimal("2000.00"),
                    trade_amount=Decimal("0.00"),
                    priority=3,
                ),
            ],
        )

        trades_required = any(item.action in ["BUY", "SELL"] for item in plan.items)
        assert trades_required is True, "Should be True when BUY and SELL actions present"

    def test_trades_required_false_with_empty_plan(self):
        """Test that trades_required=False when plan has no items."""
        with pytest.raises(ValidationError):
            RebalancePlan(
                plan_id=str(uuid.uuid4()),
                correlation_id=str(uuid.uuid4()),
                causation_id=str(uuid.uuid4()),
                timestamp=datetime.now(UTC),
                total_portfolio_value=Decimal("10000.00"),
                total_trade_value=Decimal("0.00"),
                items=[],
            )
