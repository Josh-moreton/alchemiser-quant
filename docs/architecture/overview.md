# System Architecture Overview

The Alchemiser is designed as a modular, layered system that separates concerns and enables robust automated trading.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Strategy      │    │   Execution     │    │   Data &        │
│   Layer         │    │   Layer         │    │   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Strategy Layer (`the_alchemiser/core/`)

**Purpose**: Generate trading signals based on market analysis

**Key Components**:

- `strategy_manager.py` - Orchestrates multiple strategies
- `strategy_engine.py` - Nuclear strategy implementation  
- `tecl_strategy_engine.py` - TECL momentum strategy
- `technical_indicators.py` - Market analysis tools

**Responsibilities**:

- Fetch and analyze market data
- Calculate technical indicators (RSI, moving averages)
- Generate portfolio allocation signals
- Combine multiple strategy outputs

### 2. Execution Layer (`the_alchemiser/execution/`)

**Purpose**: Execute trades and manage orders

**Key Components**:

- `trading_engine.py` - Main trading orchestrator
- `smart_execution.py` - Intelligent order placement
- `alpaca_client.py` - Direct Alpaca API wrapper
- `portfolio_rebalancer.py` - Portfolio management

**Responsibilities**:

- Transform signals into executable orders
- Place orders with smart execution logic
- Monitor order status and settlement
- Manage portfolio rebalancing

### 3. Data & Integration Layer (`the_alchemiser/utils/`)

**Purpose**: External data and service integration

**Key Components**:

- `data_provider.py` - Market data aggregation
- `real_time_pricing.py` - WebSocket price feeds
- `email_utils.py` - Notification system
- `cli_formatter.py` - User interface formatting

## Data Flow Architecture

### Signal Generation Flow

```
Market Data → Technical Analysis → Strategy Evaluation → Portfolio Signals
     ↓              ↓                     ↓                    ↓
[TwelveData]   [RSI, MA, Vol]     [Nuclear/TECL]        [Asset %]
[Alpaca API]   [Price Action]     [Market Regime]       [Weights]
```

### Order Execution Flow

```
Portfolio Signals → Order Planning → Smart Execution → Settlement
       ↓                 ↓               ↓              ↓
  [Target %]        [Buy/Sell]     [Progressive      [Position
  [Current %]       [Quantities]    Limit Orders]     Updates]
```

### Real-time Integration

```
WebSocket Feeds → Price Updates → Order Monitoring → Status Updates
      ↓               ↓               ↓                ↓
  [Bid/Ask]      [Real-time      [Fill Detection]  [Portfolio
  [Trades]        Pricing]       [Settlement]       Sync]
```

## Key Design Principles

### 1. Separation of Concerns

- **Strategy Layer**: Pure signal generation logic
- **Execution Layer**: Order management and trading mechanics  
- **Integration Layer**: External service communication

### 2. Modular Strategy System

```python
# Strategy engines are pluggable
class StrategyManager:
    def add_strategy(self, strategy: StrategyEngine, weight: float):
        """Add any strategy that implements the StrategyEngine interface"""
```

### 3. Progressive Order Execution

```python
# Smart execution tries multiple approaches
1. Limit order at mid-price (best pricing)
2. Progressive steps toward market price  
3. Market order fallback (guaranteed fill)
```

### 4. Real-time Monitoring

- WebSocket connections for live pricing
- Order status monitoring via WebSocket
- Real-time portfolio tracking

## Component Interactions

### Strategy to Execution Handoff

```python
# Strategy layer generates signals
strategy_signals = {
    "NUCLEAR": {"BIL": 0.6, "UVXY": 0.4},
    "TECL": {"TECL": 0.8, "BIL": 0.2}
}

# Execution layer receives consolidated portfolio
target_portfolio = strategy_manager.consolidate_portfolios(strategy_signals)
# Result: {"BIL": 0.4, "UVXY": 0.2, "TECL": 0.4}

# Trading engine executes rebalancing
trading_engine.rebalance_portfolio(target_portfolio)
```

### Order Execution Pipeline

```python
# 1. Portfolio Rebalancer calculates required trades
rebalancer.calculate_rebalancing_orders(current, target)

# 2. Smart Execution places orders with progressive logic
smart_execution.place_order(symbol, quantity, side)

# 3. Alpaca Client handles direct API communication
alpaca_client.place_market_order(symbol, qty, side)
```

## Scalability Considerations

### Horizontal Scaling

- Stateless strategy engines
- Configurable strategy weights
- Pluggable execution backends

### Performance Optimization

- Cached market data with TTL
- WebSocket connections for real-time data
- Async order processing capabilities

### Reliability Features

- Graceful degradation (WebSocket → REST API)
- Retry logic with exponential backoff
- Comprehensive error handling and logging

## Security Architecture

### API Key Management

- Environment variable configuration
- Separate paper/live trading credentials
- No credentials stored in code

### Trade Safety

- Paper trading by default
- Explicit live trading mode
- Position size limits and validation

### Data Protection

- No sensitive data in logs
- Secure communication with external APIs
- Local data storage only

## Next Steps

- [Execution Layer Details](./execution-layer.md)
- [Strategy Layer Details](./strategy-layer.md)
- [Data Flow Documentation](./data-flow.md)
