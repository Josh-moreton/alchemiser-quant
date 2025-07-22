# Multi-Strategy Trading System

The LQQ3 trading bot now supports running multiple strategies simultaneously with proper portfolio allocation and position tracking. This document explains how to use the new multi-strategy system.

## Overview

The multi-strategy system allows you to run multiple trading strategies in parallel:

- **Nuclear Strategy**: Original nuclear energy focused strategy
- **TECL Strategy**: Technology leverage strategy based on Composer.trade's "TECL For The Long Term"

Each strategy gets a configurable portion of your portfolio (default: 50/50 split).

## Quick Start

### Run Multi-Strategy Signals Only

```bash
python main.py multi
```

### Run Multi-Strategy Live Trading

```bash
python main.py live
```

### Run Multi-Strategy Paper Trading

```bash
python main.py paper
```

### Legacy Single Strategy Commands

```bash
python main.py bot          # Nuclear strategy only
python main.py nuclear-live # Nuclear strategy live trading
python main.py nuclear-paper # Nuclear strategy paper trading
```

## Telegram Integration

The Telegram bot now supports multi-strategy commands:

**New Commands:**

- `/nuclear` - Nuclear strategy signals only
- `/multi` - Multi-strategy signals (Nuclear + TECL)
- `/live` - Multi-strategy live trading
- `/paper` - Multi-strategy paper trading

**Legacy Commands (still supported):**

- `/bot` - Nuclear strategy only
- `/alpaca` - Redirects to multi-strategy live trading

## Architecture

### Core Components

#### 1. Strategy Manager (`core/strategy_manager.py`)

- Coordinates multiple strategies
- Manages portfolio allocation between strategies
- Tracks positions per strategy
- Consolidates signals into unified portfolio

#### 2. TECL Strategy Engine (`core/tecl_strategy_engine.py`)

- Implements "TECL For The Long Term (v7)" strategy
- Market regime detection (bull vs bear)
- Technology sector timing using XLK vs KMLM
- Volatility protection with UVXY
- Bond hedging with BIL/BSV

#### 3. Multi-Strategy Trader (`execution/multi_strategy_trader.py`)

- Enhanced Alpaca integration
- Multi-strategy execution coordination
- Comprehensive reporting and logging
- Position tracking and attribution

#### 4. Position Tracking

- Maintains separate position records per strategy
- Prevents confusion between strategy signals
- Enables performance attribution
- Stored in `/tmp/strategy_positions.json`

### Strategy Allocation

Default allocation:

- Nuclear Strategy: 50%
- TECL Strategy: 50%

This can be customized:

```python
from core.strategy_manager import MultiStrategyManager, StrategyType

manager = MultiStrategyManager({
    StrategyType.NUCLEAR: 0.6,  # 60%
    StrategyType.TECL: 0.4      # 40%
})
```

## Strategy Details

### Nuclear Strategy

- **Focus**: Nuclear energy stocks (SMR, LEU, OKLO, etc.)
- **Market Regime**: SPY vs 200-day MA
- **Overbought Protection**: RSI-based volatility hedge
- **Bear Market**: Tech/bond rotation with inverse volatility weighting

### TECL Strategy

- **Focus**: 3x leveraged technology (TECL)
- **Market Regime**: SPY vs 200-day MA  
- **Timing Signal**: XLK vs KMLM RSI comparison
- **Volatility Protection**: UVXY for extreme conditions
- **Defensive**: BIL cash equivalent

## Portfolio Construction

The system creates a consolidated portfolio by:

1. **Individual Strategy Signals**: Each strategy generates its signal independently
2. **Allocation Weighting**: Strategy signals are weighted by allocation percentage
3. **Portfolio Consolidation**: Overlapping positions are combined
4. **Position Tracking**: Each strategy's contribution is tracked separately

Example:

- Nuclear Strategy (50%): Recommends SMR 100% → 50% of total portfolio to SMR
- TECL Strategy (50%): Recommends TECL 100% → 50% of total portfolio to TECL
- **Result**: 50% SMR, 50% TECL

## Configuration

### Logging Configuration (`config.yaml`)

```yaml
logging:
  multi_strategy_alerts: "/tmp/multi_strategy_alerts.json"
  multi_strategy_log: "/tmp/multi_strategy_execution.log" 
  strategy_positions: "/tmp/strategy_positions.json"
  tecl_strategy_log: "/tmp/tecl_strategy.log"
```

### Data Requirements

The system requires market data for these symbols:

**Core Market Symbols:**

- SPY, TQQQ, SPXL (market timing)
- XLK, KMLM (sector comparison)
- UVXY (volatility hedge)
- BIL, BSV (cash equivalents)

**Strategy-Specific Symbols:**

- Nuclear: SMR, LEU, OKLO, BWXT, EXC, NLR
- TECL: TECL, SQQQ
- Supporting: IOO, VTV, XLF, VOX, QQQ, PSQ, TLT, IEF, BTAL

## Monitoring and Reporting

### Execution Logs

Multi-strategy executions are logged to:

- Console output with detailed progress
- JSON log file for programmatic analysis
- Telegram notifications with summary

### Position Tracking

Track strategy positions:

```python
from core.strategy_manager import MultiStrategyManager

manager = MultiStrategyManager()
positions = manager.get_current_positions()
summary = manager.get_strategy_performance_summary()
```

### Performance Reports

Get comprehensive performance data:

```python
from execution.multi_strategy_trader import MultiStrategyAlpacaTrader

trader = MultiStrategyAlpacaTrader(paper_trading=True)
report = trader.get_multi_strategy_performance_report()
```

## Testing

Run the comprehensive test suite:

```bash
python tests/test_multi_strategy.py
```

This tests:

- TECL strategy engine functionality
- Multi-strategy coordination
- Position tracking system
- Alpaca integration
- Configuration setup

## Migration from Single Strategy

### Existing Users

- Old commands (`/bot`, `/alpaca`) still work
- `main.py bot` and `main.py live` maintain compatibility
- Existing log files are preserved

### New Capabilities

- Run `main.py multi` to test multi-strategy signals
- Use `main.py live` for multi-strategy live trading
- Monitor via new Telegram commands

## Troubleshooting

### Common Issues

**"Import could not be resolved" errors:**

- Run from project root directory
- Ensure all dependencies installed: `pip install -r requirements.txt`

**Missing market data:**

- Check Alpaca API credentials
- Verify network connectivity
- Some symbols may have limited data availability

**Position tracking errors:**

- Check file permissions for `/tmp/strategy_positions.json`
- Ensure sufficient disk space

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Safe Testing

Always test with paper trading first:

```bash
python main.py paper
```

## Advanced Usage

### Custom Strategy Allocation

```python
from execution.multi_strategy_trader import MultiStrategyAlpacaTrader, StrategyType

trader = MultiStrategyAlpacaTrader(
    paper_trading=True,
    strategy_allocations={
        StrategyType.NUCLEAR: 0.7,  # 70%
        StrategyType.TECL: 0.3      # 30% 
    }
)

result = trader.execute_multi_strategy()
```

### Manual Strategy Execution

```python
from core.strategy_manager import MultiStrategyManager

manager = MultiStrategyManager()
strategy_signals, portfolio = manager.run_all_strategies()

# Access individual strategy results
nuclear_signal = strategy_signals[StrategyType.NUCLEAR]
tecl_signal = strategy_signals[StrategyType.TECL]
```

## Support

For issues or questions:

1. Check the test suite output: `python tests/test_multi_strategy.py`
2. Review log files in `/tmp/`
3. Enable debug logging for detailed output
4. Check GitHub Issues for known problems

The multi-strategy system provides enhanced diversification and risk management while maintaining the simplicity of the original nuclear trading bot.
