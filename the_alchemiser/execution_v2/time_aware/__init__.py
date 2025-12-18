"""Business Unit: Execution | Status: current.

Time-Aware Execution Framework
==============================

This module implements institutional-style, time-phased execution that trades off
time versus price across the trading day. Unlike the urgency-biased walk-the-book
approach, this framework:

- Avoids aggressive trading during market open (price discovery phase)
- Uses passive, price-improving behaviour during low-volatility midday periods
- Gradually increases urgency only as end-of-day deadline approaches
- Explicitly supports closing-auction participation via Alpaca's CLS time-in-force
- Minimises expected slippage rather than execution latency

Architecture
------------
The system is tick-based: EventBridge Scheduler fires every N minutes during market
hours, triggering the Execution Lambda to reassess pending orders. Each "tick" is
a scheduled wake-up call, not a stock market tick.

Phases:
1. OPEN_AVOIDANCE (09:30-10:30 ET): No aggressive execution, passive pegs only
2. PASSIVE_ACCUMULATION (10:30-14:30 ET): Small child orders, mid-peg, no crossing
3. URGENCY_RAMP (14:30-15:30 ET): Gradual peg tightening, inside-spread limits
4. DEADLINE_CLOSE (15:30-16:00 ET): Guarantee completion, CLS/MOC orders

State is persisted in DynamoDB (PendingExecutionsTable) enabling idempotent,
resumable execution across Lambda invocations.
"""

from the_alchemiser.execution_v2.time_aware.execution_policy import ExecutionPolicy
from the_alchemiser.execution_v2.time_aware.models import (
    ChildOrder,
    ExecutionPhase,
    ExecutionState,
    PendingExecution,
)
from the_alchemiser.execution_v2.time_aware.phase_detector import PhaseDetector
from the_alchemiser.execution_v2.time_aware.urgency_scorer import UrgencyScorer

__all__ = [
    "ChildOrder",
    "ExecutionPhase",
    "ExecutionPolicy",
    "ExecutionState",
    "PendingExecution",
    "PhaseDetector",
    "UrgencyScorer",
]
