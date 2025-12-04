"""Business Unit: root; Status: current.

The Alchemiser Quantitative Trading System Package.

A sophisticated multi-strategy quantitative trading system for automated portfolio management using
algorithmic trading strategies. The package supports multiple trading strategies,
real-time market data processing, and integration with
Alpaca trading platform.

Key Features:
    - Multi-strategy portfolio management (Nuclear, TECL, KLM, and DSL strategies)
    - Real-time market data processing with WebSocket integration
    - Risk management and position sizing
    - Integration with Alpaca trading platform
    - Email notifications and reporting
    - AWS Lambda deployment support
    - Full type annotations (PEP 561 compliant)

Modules:
    shared: Cross-cutting concerns (config, schemas, services, adapters)
    strategy_v2: Trading strategy engines and signals
    portfolio_v2: Portfolio management and allocation
    execution_v2: Order execution and trade management
    notifications_v2: Alert and notification services

Lambda Functions:
    Strategy Lambda: Signal generation (triggered by EventBridge Schedule)
    Portfolio Lambda: Rebalance planning (triggered by SignalGenerated events)
    Execution Lambda: Trade execution (triggered by RebalancePlanned events)
    Notifications Lambda: Email notifications (triggered by TradeExecuted/WorkflowFailed)

"""

from __future__ import annotations

__all__: list[str] = []
