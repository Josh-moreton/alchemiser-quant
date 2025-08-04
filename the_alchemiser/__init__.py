"""The Alchemiser Quantitative Trading System Package.

A sophisticated multi-strategy quantitative trading system for automated portfolio management using
algorithmic trading strategies. The package supports multiple trading strategies,
real-time market data processing, backtesting capabilities, and integration with
Alpaca trading platform.

Key Features:
    - Multi-strategy portfolio management (Nuclear and TECL strategies)
    - Real-time market data processing with WebSocket integration
    - Advanced backtesting engine with realistic execution modeling
    - Risk management and position sizing
    - Integration with Alpaca trading platform
    - Email notifications and reporting
    - AWS Lambda deployment support

Modules:
    core: Core trading logic, data providers, and utilities
    execution: Order management and portfolio rebalancing
    backtest: Backtesting engine and analysis tools
    cli: Command-line interface
    main: Application entry point
    lambda_handler: AWS Lambda integration

Example:
    Basic usage for running trading signals:
    
    >>> from the_alchemiser.main import generate_multi_strategy_signals
    >>> signals = generate_multi_strategy_signals()
    
Author: Josh Moreton
License: Private
"""
