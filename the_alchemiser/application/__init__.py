"""Business Unit: utilities; Status: current.

Execution package for The Alchemiser Quantitative Trading System.

This package handles the execution layer of the trading system, including
order management, portfolio rebalancing, and trade execution. It provides
the interface between strategy signals and actual market orders.

Modules:
    alchemiser_trader: Main trading system with multi-strategy execution
    order_manager_adapter: Compatibility adapter for order management
    simple_order_manager: Simplified order execution system
    portfolio_rebalancer: Portfolio rebalancing logic and execution

Key Features:
    - Order placement and execution
    - Portfolio rebalancing algorithms
    - Position management
    - Risk controls and validation
    - Integration with Alpaca trading platform
    - Support for both paper and live trading
"""
