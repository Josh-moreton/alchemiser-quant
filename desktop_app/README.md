# LQQ3 Trading Signal Desktop App

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run daily signal check:**
   ```bash
   python lqq3_signal_app.py
   ```

## Strategy Overview

**Binary Exit with Laddered Entry** - Optimal risk-adjusted allocation:

- **0 bullish signals** → 33% LQQ3, 67% Cash (Defensive)
- **1 bullish signal** → 66% LQQ3, 34% Cash (Balanced) 
- **2 bullish signals** → 100% LQQ3, 0% Cash (Aggressive)

## Signals

1. **MACD (12,26,9)**: Momentum indicator
   - Bullish when MACD line > Signal line
   - Fast-responding, catches early moves

2. **200-day SMA**: Trend indicator  
   - Bullish when TQQQ price > 200-day average
   - Slow-responding, confirms major trends

## Usage

Run the app daily before market open to get:
- Current signal status
- Recommended portfolio allocation  
- Signal changes from previous day
- Key levels to watch

## Performance

Historical results (2012-2025):
- **6,187% total returns** vs 5,405% buy-and-hold
- **1.15 Sharpe ratio** (excellent risk-adjusted returns)
- **-44% maximum drawdown** (vs -60% for binary allocation)
- **22 trades per year** (reasonable frequency)

## Files

- `lqq3_signal_app.py` - Main application
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

---

*Based on 12+ years of backtesting. Past performance does not guarantee future results.*
